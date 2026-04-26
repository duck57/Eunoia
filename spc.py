#! /usr/bin/env python3


from typing import SupportsFloat as Numeric
from random import shuffle
import statistics
from itertools import pairwise
from dataclasses import dataclass, InitVar
from functools import cache, cached_property
from typing import List, Literal, Tuple, Dict, Iterable
import argparse
from math import log2

NumberList = List[Numeric]
Range = Tuple[float, float]


@dataclass(frozen=True)
class SPC:
    """
    This is intended to be used on positive values.

    On the high end, the arithmetic mean and SD are used; on the low end,
    the variance and mean of the log2 values are used.  This highlights outliers
    in data sets where the data is bimodal and using the arithmetic values
    typically puts the thresholds in the negative realm.

    TODO: clean unused properties and simplify.
    """

    raw_data: NumberList
    display: InitVar[bool] = False
    rounding: int = 2
    magic_constant = 2.66
    ordering: Literal["sort", "shuffle", "original"] = "shuffle"
    shuffle_replicates: int = 100
    tabwidth = 11

    @cached_property
    def log_spc(self) -> "SPC":
        return SPC(
            [log2(abs(x)) for x in self.raw_data],
            rounding=self.rounding,
            shuffle_replicates=self.shuffle_replicates,
        )

    @cached_property
    def inverse_spc(self) -> "SPC":
        return SPC(
            [1 / x for x in self.raw_data],
            shuffle_replicates=self.shuffle_replicates,
            rounding=5,
        )

    @cached_property
    def shuffled_data(self) -> NumberList:
        if self.ordering == "original":
            return self.raw_data
        if self.ordering == "sort":
            return sorted(self.raw_data)
        # duplicate the data set for small sets w/ large range
        d = self.raw_data[:] * self.shuffle_replicates
        shuffle(d)
        return d

    def __post_init__(self, display):
        if l := len(self.raw_data) < 1:
            raise ValueError(f"Insufficient data set to analyze: n={l}" + f" (min = 2)")
        if not display:
            return
        self.print()

    def round_dict(self, d: Dict[..., float]) -> Dict[..., float]:
        return {key: round(value, self.rounding) for key, value in d.items()}

    @cached_property
    def vals(self) -> Dict[str, float]:
        """In retrospect, shold be called "thresholds\" """
        return self.round_dict(
            {
                "-3σ": self.three_sd[0],
                "-SPC": self.spc_thresholds[0],
                "-2σ": self.two_sd[0],
                "med": self.median,
                "mean": self.a_mean,
                "mR": self.mR,
                "psd": self.sd,
                "+2σ": self.two_sd[1],
                "+SPC": self.spc_thresholds[1],
                "+3σ": self.three_sd[1],
            }
        )

    @cached_property
    def raw_thresholds(self) -> Dict[str, float]:
        return self.round_dict(
            {
                "-3σ": self.three_sd[0],
                "-SPC": self.spc_thresholds[0],
                "-2σ": self.two_sd[0],
                "+2σ": self.two_sd[1],
                "+SPC": self.spc_thresholds[1],
                "+3σ": self.three_sd[1],
            }
        )

    @cached_property
    def logvalues(self) -> Dict[str, float]:
        return self.log_spc.vals

    @cached_property
    def geo_vals(self) -> Dict[str, float]:
        return self.round_dict({key: 2**x for key, x in self.log_spc.vals.items()})

    @cached_property
    def inv_vals(self) -> Dict[str, float]:
        return self.round_dict({key: 1 / x for key, x in self.inverse_spc.vals.items()})

    @cached_property
    def mixed_thresholds(self) -> Dict[str, float]:
        """Uses geo mean on the low end and arithmetic on the high"""
        return self.round_dict(
            {
                "-3σ": self.geo_vals["-3σ"],
                "-SPC": self.geo_vals["-SPC"],
                "-2σ": self.geo_vals["-2σ"],
                "+2σ": self.vals["+2σ"],
                "+SPC": self.vals["+SPC"],
                "+3σ": self.vals["+3σ"],
            }
        )

    @cached_property
    def centers(self) -> Dict[str, float]:
        return self.round_dict(
            {
                "a. mean": self.a_mean,
                "median": self.median,
                # "mR": self.mR,
                # "SD": self.sd,
                "geo mean": self.geo_mean,
                "h. mean": self.harmonic_mean,
                "log mean": self.geo_vals["mean"],
            }
        )

    def tabstring(self, s: Iterable, header: str = "", end: str = "") -> str:
        s = [str(x) for x in s]
        if header:
            s = [header] + s
        if end:
            s = s + [end]
        return "\t".join(s).expandtabs(self.tabwidth)

    @cached_property
    def a_mean(self) -> float:
        return statistics.fmean(self.raw_data)

    @cached_property
    def geo_mean(self) -> float:
        return statistics.geometric_mean(self.raw_data)

    @cached_property
    def harmonic_mean(self) -> float:
        return statistics.harmonic_mean(self.raw_data)

    @cached_property
    def mR(self) -> float:
        return statistics.fmean([abs(y - x) for x, y in pairwise(self.shuffled_data)])

    @cached_property
    def median(self) -> float:
        return statistics.median(self.raw_data)

    @cached_property
    def sd(self) -> float:
        return statistics.pstdev(self.raw_data)

    def thresholds(self, width: Numeric) -> Range:
        return self.a_mean - width, self.a_mean + width

    @cached_property
    def spc_thresholds(self) -> Range:
        return self.thresholds(self.magic_constant * self.mR)

    @cached_property
    def two_sd(self) -> Range:
        return self.thresholds(2 * self.sd)

    @cached_property
    def three_sd(self) -> Range:
        return self.thresholds(3 * self.sd)

    def outliers(self, lo: Numeric, hi: Numeric) -> NumberList:
        return [x for x in self.raw_data if x < lo or x > hi]

    def abs_outliers(self, lo: Numeric, hi: Numeric) -> NumberList:
        return [x for x in self.raw_data if abs(x) < lo or abs(x) > hi]

    def outs(self, width: Numeric) -> NumberList:
        return self.outliers(*self.thresholds(width))

    @cached_property
    def harm_mean(self) -> float:
        return round(statistics.harmonic_mean(self.raw_data), 1)

    @cached_property
    def detail_str(self) -> str:
        return "\n".join(
            [
                # self.tabstring(self.inv_vals.values(), "harm", "harm"),
                # self.tabstring(self.inverse_spc.vals.values(), "1/x", "1/x"),
                self.tabstring(self.geo_vals.values(), "geo", "geo"),
                self.tabstring(self.logvalues.values(), "log2", "log2"),
                self.tabstring(self.vals.values(), "raw", "raw"),
                self.tabstring(self.vals.keys(), "type", "type"),
                f"\tn={len(self.raw_data)}\t∑={sum(self.raw_data)}",
                f"2σ outliers\t{self.outs(2 * self.sd)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.two_sd))}",
                f"3σ outliers\t{self.outs(3 * self.sd)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.three_sd))}",
                f"SPC outliers\t{self.outs(self.magic_constant * self.mR)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.spc_thresholds))}",
            ]
        )

    @cached_property
    def stats_str(self) -> str:
        return "\n".join(
            [
                self.tabstring(self.centers.values(), "      "),
                self.tabstring(self.centers.keys(), "centers", "centers"),
                "\t".join(
                    [
                        "",
                        f"n={len(self.raw_data)}",
                        f"∑={sum(self.raw_data)}",
                        f"SD={round(self.sd, self.rounding)}",
                        f"mR={round(self.mR, self.rounding)}",
                    ]
                ),
                self.tabstring(self.mixed_thresholds.values(), "thresholds"),
                self.tabstring(self.raw_thresholds.keys(), "     ", "thresholds"),
            ]
        )

    def outlier_string(self, s: str) -> str:
        return f"{s}\t{self.get_outliers(s)}"

    def get_outliers(self, s: str) -> NumberList:
        return self.abs_outliers(
            self.mixed_thresholds[f"-{s}"],
            self.mixed_thresholds[f"+{s}"],
        )

    @cached_property
    def print_str(self) -> str:
        return "\n".join(
            [
                self.stats_str,
                "***\tOUTLIERS\t***",
                self.outlier_string("2σ"),
                self.outlier_string("SPC"),
                self.outlier_string("3σ"),
            ]
        )

    def print(self) -> None:
        print(self.print_str)


def exp_range(r: Range) -> Range:
    return 2 ** r[0], 2 ** r[1]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("data", nargs="*", type=float)
    p.add_argument(
        "-s", "--ordering", choices=["sort", "shuffle", "original"], default="shuffle"
    )
    p.add_argument("-n", "--random-iterations", type=int, default=69)
    p.add_argument("-d", "--rounding", type=int, default=1)
    args = p.parse_args()
    SPC(
        args.data,
        display=True,
        ordering=args.ordering,
        shuffle_replicates=args.random_iterations,
        rounding=args.rounding,
    )
