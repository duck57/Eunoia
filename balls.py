#! /usr/bin/env python3

import random

SPORTS_BALLS = "🏐🎾🏀🏈🥎⚾️⚽️🏉".strip()
OTHER_BALLS = "🎱🪩🔮🧶".strip()
ALL_BALLS = list(SPORTS_BALLS + OTHER_BALLS)

random.shuffle(ALL_BALLS)

print("".join(ALL_BALLS))
