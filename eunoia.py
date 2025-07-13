#!/usr/bin/env python3

"""
eunoia.py

Filter an input dictionary into words which would fit the rules for inclusion
in Christian Bök's Eunoia.  
"""

from collections import Counter, defaultdict
from typing import *
import click


DEFAULT_VOWEL_STRING, DEFAULT_Y_STRING = "AEIOU", "Y"


def setup_vowels(
    vowels: str = DEFAULT_VOWEL_STRING, forbidden: str = DEFAULT_Y_STRING
) -> Tuple[set[str], set[str]]:
    return set(vowels.upper().strip()), set(forbidden.upper().strip())


DEFAULT_VOWEL_SET, DEFAULT_Y_SET = setup_vowels()


def analyze_word(
    word: str, vowels: set[str] = DEFAULT_VOWEL_SET, forbidden: set[str] = DEFAULT_Y_SET
) -> Tuple[Union[str, None, Literal[False]], str]:
    """
    Returns a tuple:
    1. Returns the vowel if monovocalic, True if no vowels at all, or False if mixed vowels
    2. True if a forbidden letter is contained, false otherwise
    """
    letters = set(word.upper().strip())
    v_lst = "".join(letters & vowels)
    f_lst = "".join(letters & forbidden)
    # print(f"{v_lst=} {f_lst=}")
    if not v_lst:  # no vowels
        return None, f_lst
    if len(v_lst) > 1:  # multiple vowels
        return False, f_lst
    return v_lst, f_lst  # only one vowel


@click.command()
@click.argument("dic", type=click.File(), default="/usr/share/dict/words")
@click.option(
    "-v",
    "--vowels",
    type=click.STRING,
    default=DEFAULT_VOWEL_STRING,
    help="List of vowels",
)
@click.option(
    "-f",
    "--forbidden",
    type=click.STRING,
    default=DEFAULT_Y_STRING,
    help="Letters to avoid",
)
@click.option(
    "-h",
    "hide_stats",
    type=click.BOOL,
    is_flag=True,
    flag_value=False,
    help="hide the output",
)
def parse_dictionary(
    dic: Iterable[str],
    vowels: str = DEFAULT_VOWEL_STRING,
    forbidden: str = DEFAULT_Y_STRING,
    hide_stats: bool = True,
) -> Tuple[Dict, Dict]:
    """
    Parses the input dictionary

    Returns two dicts, both of the form Dict[chr, List[str]]
    The first dict is of the monovocalic words
    The second dict is of words that would have made it into the first
    dict if not for the presence of a forbidden letter.
    """
    word_list = defaultdict(list)
    filtered = defaultdict(list)
    vowel_set, forbidden_set = setup_vowels(vowels, forbidden)
    stats = Counter()
    for word in dic:
        word = word.strip()
        vowel, y = analyze_word(word, vowel_set, forbidden_set)
        stats["total"] += 1  # total words analyzed
        if vowel is False:  # vowel is None = no vowels
            stats["N/A"] += 1  # words with multiple vowels
            continue
        stats["monovocalic"] += 1  # words with a single vowel
        if y:
            stats["removed"] += 1  # words with surpressed letters
            filtered[vowel].append(word)
        else:
            stats["pure vowel"] += 1  # pure
            word_list[vowel].append(word)
    if not hide_stats:
        for v in list(vowel_set) + [None]:
            print(f"{v}: {len(word_list[v])} + {len(filtered[v])} filtered")
        for stat in stats.keys():
            print(f"{stat}: {stats[stat]}")
    return word_list, filtered


if __name__ == "__main__":
    parse_dictionary()
