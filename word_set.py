#! /usr/bin/env python3.13

import argparse


Dictionary = dict[str, set]


def load_words(path: str = "/usr/share/dict/words") -> Dictionary:
    f = open(path)
    words: Dictionary = {}
    for w in f:
        w = w.lower().strip()
        words[w] = set(w)
    f.close()
    return words


def match_words(allowed_letters: str, dictionary: Dictionary) -> list[str]:
    allowed_letters = set(allowed_letters.lower().strip())
    return [word for word in dictionary if dictionary[word] <= allowed_letters]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("letters", type=str)
    p.add_argument("-d", type=str, default="/usr/share/dict/words")
    args = p.parse_args()
    d = load_words(args.d)
    words = match_words(args.letters, d)
    print("\t".join(words))
    print(f"\n{len(words)}\t{args.letters}\t{args.d}")
