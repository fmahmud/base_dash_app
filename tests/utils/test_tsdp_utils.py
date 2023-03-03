import datetime
import random

from dateutil.relativedelta import relativedelta

from base_dash_app.utils import tsdp_utils
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


def test_interpolate_tsdp_array_1_1():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2022, 1, 1)
    array = []
    latest_val_before_start = 1
    result = tsdp_utils.interpolate_tsdp_array(array, start_date, end_date, latest_val_before_start)
    assert len(result) == 365
    assert result[0].value == 1


def test_interpolate_tsdp_array_1_2():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2022, 1, 1)
    array = [TimeSeriesDataPoint(datetime.datetime(2021, 5, 1), 100)]
    latest_val_before_start = 1
    result = tsdp_utils.interpolate_tsdp_array(array, start_date, end_date, latest_val_before_start)
    assert 365 == len(result)
    assert 1 == result[0].value
    assert 100 == result[-1].value


def test_interpolate_tsdp_array_1_3():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2022, 1, 1)
    latest_val_before_start = 1
    first_val = 100
    second_val = 200
    array = [
        TimeSeriesDataPoint(datetime.datetime(2021, 5, 1), first_val),
        TimeSeriesDataPoint(datetime.datetime(2021, 8, 1), second_val)
    ]
    first_index = (array[0].date - start_date).days
    second_index = (array[1].date - start_date).days
    result = tsdp_utils.interpolate_tsdp_array(array, start_date, end_date, latest_val_before_start)
    assert result is not None
    assert 365 == len(result)
    assert latest_val_before_start == result[0].value
    assert latest_val_before_start == result[first_index - 1].value
    assert first_val == result[first_index].value
    assert first_val == result[second_index - 1].value
    assert second_val == result[second_index].value
    assert second_val == result[-1].value


def test_interpolate_tsdp_array_2_1():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2021, 1, 2)
    latest_val_before_start = 1
    array = []
    result = tsdp_utils.interpolate_tsdp_array(
        array, start_date, end_date, latest_val_before_start,
        interval_size=relativedelta(hours=1)
    )

    assert len(result) == 24
    assert result[0].value == latest_val_before_start
    assert result[-1].value == latest_val_before_start


def test_interpolate_tsdp_array_2_2():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2021, 1, 2)
    latest_val_before_start = 1
    second_val = 100
    array = [TimeSeriesDataPoint(datetime.datetime(2021, 1, 1, hour=5), second_val)]
    result = tsdp_utils.interpolate_tsdp_array(
        array, start_date, end_date, latest_val_before_start,
        interval_size=relativedelta(hours=1)
    )
    assert len(result) == 24
    assert latest_val_before_start == result[0].value
    assert latest_val_before_start == result[4].value
    assert second_val == result[5].value
    assert second_val == result[-1].value

def test_interpolate_tsdp_array_2_3():
    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2021, 1, 2)
    latest_val_before_start = 1
    first_val = 100
    second_val = 200
    array = [
        TimeSeriesDataPoint(datetime.datetime(2021, 1, 1, hour=5), first_val),
        TimeSeriesDataPoint(datetime.datetime(2021, 1, 1, hour=10), second_val)
    ]

    first_index = (array[0].date - start_date).seconds // 3600
    second_index = (array[1].date - start_date).seconds // 3600

    result = tsdp_utils.interpolate_tsdp_array(
        array, start_date, end_date, latest_val_before_start,
        interval_size=relativedelta(hours=1)
    )

    assert len(result) == 24
    assert latest_val_before_start == result[0].value
    assert latest_val_before_start == result[first_index - 1].value
    assert first_val == result[first_index].value
    assert first_val == result[second_index - 1].value
    assert second_val == result[second_index].value
    assert second_val == result[-1].value


def test_get_max_for_each_moment_1_1():
    # create 2 lists of 10 TimeSeriesDataPoint objects
    # each list has the same moments,
    # but list 1 has lower values than list 2 for each moment.

    # list 1
    list_1 = [TimeSeriesDataPoint(
        date=datetime.datetime(2021, 1, 1 + i),
        value=random.randint(1, 100)
    ) for i in range(10)]

    list_2 = [TimeSeriesDataPoint(
        date=datetime.datetime(2021, 1, 1 + i),
        value=random.randint(100, 200)
    ) for i in range(10)]

    max_values = tsdp_utils.get_max_for_each_moment([list_1, list_2])

    assert max_values is not None
    assert len(max_values) == 10
    assert all([max_values[i].value == max(list_1[i].value, list_2[i].value) for i in range(10)])




