import datetime
import json
from typing import List, Union

from dateutil.relativedelta import relativedelta

from base_dash_app.utils import file_utils
from base_dash_app.utils.date_utils import enumerate_datetimes_between
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


def interpolate_tsdp_array(
    array: List[TimeSeriesDataPoint],
    first_moment: datetime.datetime,
    last_moment: datetime.datetime,
    latest_val_before_start,
    interval_size: relativedelta = relativedelta(days=1),
):
    all_moments = enumerate_datetimes_between(first_moment, last_moment, interval_size)
    now = datetime.datetime.now()
    num_seconds_in_interval = int((now + interval_size - now).total_seconds())

    # map each tsdp to a time segment of interval_size
    time_segment_to_tsdp_map = {moment: None for moment in all_moments}
    for tsdp in sorted(array):
        seconds_since_first = (tsdp.date - first_moment).total_seconds()
        tsdp_index = int(seconds_since_first // num_seconds_in_interval)
        time_segment_to_tsdp_map[all_moments[tsdp_index]] = tsdp

    # fill in gaps
    result_array = []
    for moment in all_moments:
        if moment in time_segment_to_tsdp_map and time_segment_to_tsdp_map[moment] is not None:
            result_array.append(time_segment_to_tsdp_map[moment])
        else:
            if len(result_array) > 0:
                result_array.append(TimeSeriesDataPoint(moment, result_array[-1].value))
            else:
                result_array.append(TimeSeriesDataPoint(moment, latest_val_before_start))

    return result_array


def get_max_for_each_moment(array: List[List[TimeSeriesDataPoint]]):
    max_for_each_moment = {}
    for series in array:
        for dp in series:
            if dp.date in max_for_each_moment:
                max_for_each_moment[dp.date] = (
                    dp if dp.value > max_for_each_moment[dp.date].value else max_for_each_moment[dp.date]
                )
            else:
                max_for_each_moment[dp.date] = dp

    return list(max_for_each_moment.values())


def serialize_tsdp(tsdp: TimeSeriesDataPoint):
    return tsdp.to_dict()


def serialize_tsdp_array(tsdp_array: List[TimeSeriesDataPoint]):
    return [serialize_tsdp(tsdp) for tsdp in tsdp_array]


def tsdp_array_to_json(tsdp_array: List[TimeSeriesDataPoint]):
    return json.dumps(serialize_tsdp_array(tsdp_array))


def tsdp_array_to_csv(tsdp_array: List[TimeSeriesDataPoint]):
    return file_utils.convert_dict_to_csv(
        data_to_write=serialize_tsdp_array(tsdp_array),
        keys=["date", "value"],
    )