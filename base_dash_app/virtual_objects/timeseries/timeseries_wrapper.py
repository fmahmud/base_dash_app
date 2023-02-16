from typing import List

from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpStatCardDescriptor
from base_dash_app.virtual_objects.timeseries.abstract_timeseries_wrapper import AbstractTimeSeriesWrapper


class TimeSeriesWrapper(AbstractTimeSeriesWrapper):
    def get_description(self):
        return self.description

    def get_title(self):
        return self.title

    def get_unique_id(self):
        return self.unique_id

    def get_stat_card_descriptors(self):
        return self.stat_card_descriptors

    def get_show_in_datatable(self):
        return self.show_in_datatable

    def get_column_format(self):
        return self.column_format

    def get_column_datatype(self):
        return self.column_datatype

    def __init__(
            self, title: str, unique_id: str,
            stat_card_descriptors: List[TsdpStatCardDescriptor] = None,
            show_in_datatable=True, column_format=None, column_datatype="numeric",
            description=None,
    ):
        super().__init__()
        self.title = title
        self.unique_id = unique_id
        self.stat_card_descriptors: List[TsdpStatCardDescriptor] = stat_card_descriptors or []
        self.show_in_datatable = show_in_datatable
        self.column_format = column_format
        self.column_datatype = column_datatype
        self.description = description
