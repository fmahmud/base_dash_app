import abc

from base_dash_app.virtual_objects.timeseries.time_series import AbstractTimeSeries


class AbstractTimeSeriesWrapper(AbstractTimeSeries, abc.ABC):
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def get_stat_card_descriptors(self):
        pass

    @abc.abstractmethod
    def get_show_in_datatable(self):
        pass

    @abc.abstractmethod
    def get_column_format(self):
        pass

    @abc.abstractmethod
    def get_column_datatype(self):
        pass

