import datetime
from abc import ABC
from typing import List

from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent, CachedResultableEvent
from base_dash_app.virtual_objects.statistics.statistic import Statistic
from base_dash_app.virtual_objects.statistics.statistic_over_time import StatisticOverTime
from base_dash_app.virtual_objects.statistics.streaks import BestStreak, WorstStreak
from base_dash_app.virtual_objects.statistics.success_ratio import SuccessRatio


# todo: move this out
class ResultableEventSeries(ABC):
    def __init__(self, *, statistics: List[Statistic] = None,
                 stats_over_time: List[StatisticOverTime] = None):
        self.events: List[ResultableEvent] = []

        self.success_events: List[ResultableEvent] = []
        self.warning_events: List[ResultableEvent] = []
        self.failed_events: List[ResultableEvent] = []
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
            self.uncategorized_events.append(cached_result)
        elif cached_result.result < 0:
            self.failed_events.append(cached_result)
        elif cached_result.result == 0:
            self.warning_events.append(cached_result)
        else:
            self.success_events.append(cached_result)

        self.compute_stats_for_result(cached_result.result, cached_result.get_date())

    def process_result(self, result: float, resultable_event: ResultableEvent):
        cached_result = CachedResultableEvent(result, resultable_event.get_date(), original_re=resultable_event)
        self.process_cached_result(cached_result)
        return cached_result
