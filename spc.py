#! /usr/bin/env python3


from typing import SupportsFloat as Numeric
from random import shuffle
import statistics
from itertools import pairwise
from dataclasses import dataclass, InitVar
from functools import cached_property
from typing import List, Literal, Tuple, Dict, Iterable
import argparse
from math import log2

NumberList = List[Numeric]
Range = Tuple[float, float]


@dataclass(frozen=True)
class SPC:
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
        return self.round_dict(
            {
                "-3σ": self.three_sd[0],
                "-SPC": self.spc_thresholds[0],
                "-2σ": self.two_sd[0],
                "med": statistics.median(self.raw_data),
                "mean": self.mean,
                "mR": self.mR,
                "psd": self.sd,
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

    def tabstring(self, s: Iterable) -> str:
        return "\t".join(str(x) for x in s).expandtabs(self.tabwidth)

    @cached_property
    def mean(self) -> float:
        return statistics.mean(self.raw_data)

    @cached_property
    def mR(self) -> float:
        return statistics.mean([abs(y - x) for x, y in pairwise(self.shuffled_data)])

    @cached_property
    def sd(self) -> float:
        return statistics.pstdev(self.raw_data)

    def thresholds(self, width: Numeric) -> Range:
        return self.mean - width, self.mean + width

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
    def print_str(self) -> str:
        return "\n".join(
            [
                self.tabstring(self.geo_vals.values()),
                self.tabstring(self.logvalues.values()),
                self.tabstring(self.vals.values()),
                self.tabstring(self.vals.keys()),
                f"\tn={len(self.raw_data)}\t∑={sum(self.raw_data)}",
                f"2σ outliers\t{self.outs(2 * self.sd)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.two_sd))}",
                f"3σ outliers\t{self.outs(3 * self.sd)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.three_sd))}",
                f"SPC outliers\t{self.outs(self.magic_constant * self.mR)}",
                f"\tlog\t{self.abs_outliers(*exp_range(self.log_spc.spc_thresholds))}",
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
    p.add_argument("-d", "--rounding", type=int, default=2)
    args = p.parse_args()
    SPC(
        args.data,
        display=True,
        ordering=args.ordering,
        shuffle_replicates=args.random_iterations,
        rounding=args.rounding,
    )
