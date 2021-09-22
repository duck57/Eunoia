#!/usr/bin/env python3

"""
eunoia.py

Filter an input dictionary into words which would fit the rules for inclusion
in Christian Bök's Eunoia.  
"""

from collections import Counter, defaultdict
from typing import *
import click


def setup_vowels(vowels: Optional[str], forbidden: Optional[str]) -> Tuple[str, str]:
    if vowels is None:
        vowels = "AEIOU"
    if forbidden is None:
        forbidden = "Y"
    return vowels.upper(), forbidden.upper()


def analyze_word(
    word: str, vowels: str = None, forbidden: str = None, preset: bool = False
) -> Tuple[Union[chr, bool], bool]:
    """
    :param preset: has setup_vowels/2 been set up in a previous call?
    Returns a tuple:
    1. Returns the vowel if monovocalic, True if no vowels at all, or False if mixed vowels
    2. True if a forbidden letter is contained, false otherwise
    """
    if not preset:  # no need to do this when looping
        vowels, forbidden = setup_vowels(vowels, forbidden)
    word = word.upper().strip()
    letters = Counter(word)
    v_lst = "".join([v for v in vowels if letters[v] > 0])
    f_lst = "".join([f for f in forbidden if letters[f] > 0])
    # print(f"{v_lst=} {f_lst=}")
    if not v_lst:  # no vowels
        return True, bool(f_lst)
    if len(v_lst) > 1:  # multiple vowels
        return False, bool(f_lst)
    return v_lst, bool(f_lst)


@click.command()
@click.argument("dic", type=click.File())
@click.option(
    "-v", "--vowels", type=click.STRING, default="AEIOU", help="List of vowels"
)
@click.option(
    "-f", "--forbidden", type=click.STRING, default="Y", help="Letters to avoid"
)
@click.option("-h", "show_stats", type=click.BOOL, is_flag=True, flag_value=False)
# @click.option("-o", type=click.File(), default=None)
def parse_dictionary(
    dic: Iterable[str],
    vowels: str = None,
    forbidden: str = None,
    show_stats: bool = False,
) -> Tuple[Dict, Dict]:
    """
    Parses the input dictionary

    Returns two dicts, both of the form Dict[chr, List[str]]
    The first dict is of the monovocalic words
    The second dict is of words that would have made it into the first
    dict if not for the presence of r forbidden letter
    """
    word_list = defaultdict(list)
    filtered = defaultdict(list)
    vowels, forbidden = setup_vowels(vowels, forbidden)
    stats = Counter()
    for word in dic:
        word = word.strip()
        vowel, y = analyze_word(word, vowels, forbidden, True)
        stats["total"] += 1  # total words analyzed
        if not vowel:
            stats["N/A"] += 1  # words with multiple vowels
            continue
        stats["monovocalic"] += 1  # words with a single vowel
        if y:
            stats["removed"] += 1  # words with surpressed letters
            filtered[vowel].append(word)
        else:
            stats["pure vowel"] += 1  # pure
            word_list[vowel].append(word)
    if show_stats or True:  # always show stats for now
        # print(f"{word_list}\n{filtered}\n{stats}")
        vl = list(vowels)
        vl.append(True)
        for v in vl:
            print(f"{v}: {len(word_list[v])} + {len(filtered[v])} filtered")
        for stat in stats.keys():
            print(f"{stat}: {stats[stat]}")
    return word_list, filtered


if __name__ == "__main__":
    parse_dictionary()
