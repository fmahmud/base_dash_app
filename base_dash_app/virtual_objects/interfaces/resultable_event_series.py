import datetime
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Type, Hashable, Dict

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent, CachedResultableEvent
from base_dash_app.virtual_objects.result import Result
from base_dash_app.virtual_objects.statistics.statistic import Statistic
from base_dash_app.virtual_objects.statistics.statistic_over_time import StatisticOverTime
from base_dash_app.virtual_objects.statistics.streaks import BestStreak, WorstStreak
from base_dash_app.virtual_objects.statistics.success_ratio import SuccessRatio


class Comparable(ABC):
    @abstractmethod
    def __le__(self, other):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass


class Index(Comparable, ABC):
    @abstractmethod
    def __hash__(self):
        pass


class Aggregatable(Comparable, ABC):
    @abstractmethod
    def __add__(self, other):
        pass

    @abstractmethod
    def __radd__(self, other):
        pass

    @abstractmethod
    def __sub__(self, other):
        pass

    @abstractmethod
    def __rsub__(self, other):
        pass


class Series(ABC):
    def __init__(self, index_type: Type[Index], data_type: Type[Aggregatable]):
        self.index_type: Type[Index] = index_type
        self.data_type: Type[Aggregatable] = data_type

        # todo...


class ResultableEventSeries(ABC):
    """
    A container for a list of ResultableEvents to create a series.
    A series has an index, in the case of a TimeSeries the time is the index, and some data stored for that index.
    The interface the series provides focuses on getting data based on that index:
        at a particular index, before, or after.
    """

    def __init__(self, *, statistics: List[Statistic] = None,
                 stats_over_time: List[StatisticOverTime] = None):
        self.events: List[ResultableEvent] = []

        self.success_events: List[ResultableEvent] = []
        self.warning_events: List[ResultableEvent] = []
        self.failed_events: List[ResultableEvent] = []
        self.in_progress_events: List[ResultableEvent] = []
        self.uncategorized_events: List[ResultableEvent] = []

        self.statistics: List[Statistic] = statistics if statistics is not None else []
        self.stats_over_time: List[StatisticOverTime] = stats_over_time if stats_over_time is not None else []
        self.success_ratio: SuccessRatio = SuccessRatio()
        self.success_ratio_over_time: StatisticOverTime = StatisticOverTime(self.success_ratio)

        self.best_streak: BestStreak = BestStreak()
        self.worst_streak: WorstStreak = WorstStreak()

        self.subseries = []

    def create_subseries_for_date_range(self, start: datetime.datetime, end: datetime.datetime):
        new_series = ResultableEventSeries()
        new_series.statistics = [type(s)() for s in self.statistics]
        new_series.stats_over_time = [type(s)(s.statistic) for s in self.stats_over_time]

        for event in self.events:
            event: CachedResultableEvent
            if start <= event.date <= end:
                new_series.process_cached_result(event)

        self.subseries.insert(0, new_series)
        return new_series

    def compute_stats_for_result(self, result: float, date: datetime.datetime):
        # todo: convert to not use float result - use Result or StatusesEnum instead
        if result is None:
            return

        for stat in self.statistics:
            stat.process_result(result)

        for stat in self.stats_over_time:
            stat.process_result(result, date)

        self.success_ratio_over_time.process_result(result, date)
        self.best_streak.process_result(result)
        self.worst_streak.process_result(result)

    def process_cached_result(self, cached_result: CachedResultableEvent):
        self.events.append(cached_result)
        self.events = sorted(self.events)

        if cached_result.result is None:
            result_status = StatusesEnum.PENDING
        else:
            result_status = cached_result.result.status

        if result_status == StatusesEnum.IN_PROGRESS:
            self.uncategorized_events.append(cached_result)
        elif result_status == StatusesEnum.FAILURE:
            self.failed_events.append(cached_result)
        elif result_status == StatusesEnum.WARNING:
            self.warning_events.append(cached_result)
        elif result_status == StatusesEnum.SUCCESS:
            self.success_events.append(cached_result)
        else:
            self.uncategorized_events.append(cached_result)

        self.compute_stats_for_result(cached_result.result.result, cached_result.get_date())

    def process_result(self, result: Result, resultable_event: ResultableEvent):
        cached_result = CachedResultableEvent(result, resultable_event.get_date(), original_re=resultable_event)
        self.process_cached_result(cached_result)
        return cached_result


class CachedResultableEventSeries(ResultableEventSeries):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.events: List[CachedResultableEvent] = []

    def process_result(self, result: Result, resultable_event: ResultableEvent):
        if type(resultable_event) != CachedResultableEvent and not isinstance(resultable_event, CachedResultableEvent):
            raise Exception(
                f"Trying to process resultable event of type {type(resultable_event)} instead of CachedResultableEvent"
            )

        resultable_event: CachedResultableEvent
        self.process_cached_result(resultable_event)
        return resultable_event
