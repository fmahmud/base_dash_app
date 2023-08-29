from enum import Enum
from functools import partial


class TsdpAggregationFuncs(Enum):
    MEAN = partial(
        lambda list_of_tsdps:
            sum([x.value for x in list_of_tsdps])
            / (len(list_of_tsdps) if len(list_of_tsdps) > 0 else 1)
    )
    MODE = partial(
        lambda list_of_tsdps: max(set([x.value for x in list_of_tsdps]), key=list_of_tsdps.count)
    )
    MEDIAN = partial(
        lambda list_of_tsdps: (
            sorted(list_of_tsdps, key=lambda t: t.value)[len(list_of_tsdps) // 2]
        ) if len(list_of_tsdps) > 0 else None
    )
    SUM = partial(
        lambda list_of_tsdps: sum([x.value for x in list_of_tsdps])
    )
    MIN = partial(
        lambda list_of_tsdps: min([x.value for x in list_of_tsdps])
    )
    MAX = partial(
        lambda list_of_tsdps: max([x.value for x in list_of_tsdps])
    )
    COUNT = partial(
        lambda list_of_tsdps: len(list_of_tsdps)
    )
    LATEST_VALUE = partial(
        lambda list_of_tsdps: sorted(list_of_tsdps)[-1].value if len(list_of_tsdps) > 0 else None
    )
    SEGMENT_START = partial(
        lambda list_of_tsdps: sorted(list_of_tsdps)[0].value if len(list_of_tsdps) > 0 else None
    )

    def __call__(self, *args):
        return self.value(*args)