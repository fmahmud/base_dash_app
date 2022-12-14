import math
from typing import List, Set
from collections import Counter

ELO_K = 80
SIMPLE_DATE_FORMAT = "%d %b %Y"


def apply_all_to_dict(a: dict, **kwargs):
    for k, v in kwargs.items():
        a[k] = v
    return a


def apply(a: dict, b: dict):
    if a is None and b is not None:
        return b

    if b is None and a is not None:
        return a

    if a is None and b is None:
        return None

    to_return = dict(a)
    for k, v in b.items():
        to_return[k] = v

    return to_return


def replace_last(string, delimiter, replacement):
    if delimiter not in string:
        return string

    start, _, end = string.rpartition(delimiter)
    return start + replacement + end


def get_n_sized_permutations(items, size) -> List[List]:
    if size == 1:
        return [[item] for item in items]

    items_below = get_n_sized_permutations(items, size - 1)

    result = []
    for below_item in items_below:
        for item in items:
            new_item = below_item.copy()
            new_item.append(item)
            result.append(new_item)

    return result


def get_n_sized_combinations(items, size) -> List[List]:
    if size == 1:
        return [[item] for item in items]

    items_below = get_n_sized_combinations(items, size - 1)
    print("size(%i) = %s" % (size - 1, items_below))
    result = []

    for i in range(0, len(items_below)):
        for j in range(min(i, len(items) - 1), len(items)):
            new_item = Counter(items_below[i]) + Counter({items[j]: 1})
            result.append(list(new_item.elements()))

    return result


def get_expected_result_from_elo(player_elo: float, opponent_elo: float) -> float:
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))


def update_elo(player_elo: float, opponent_elo: float, won: bool) -> float:
    expected_result = get_expected_result_from_elo(player_elo, opponent_elo)

    new_elo_for_player = player_elo + ELO_K * ((1 if won else 0) - expected_result)
    return new_elo_for_player


