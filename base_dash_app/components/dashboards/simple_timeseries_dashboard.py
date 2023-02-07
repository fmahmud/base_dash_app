import datetime
import time
from typing import List, Callable, Dict, Optional

from dash.exceptions import PreventUpdate
from dash import html, dcc

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpSparklineStatCard
from base_dash_app.components.datatable.download_and_reload_bg import construct_down_ref_btgrp
from base_dash_app.components.datatable.time_series_datatable_wrapper import TimeSeriesDataTableWrapper
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncHandlerService, AsyncWorkProgressContainer
from base_dash_app.utils.file_utils import convert_dict_to_csv
from base_dash_app.virtual_objects.timeseries.abstract_timeseries_wrapper import AbstractTimeSeriesWrapper
from base_dash_app.virtual_objects.timeseries.date_range_aggregation_descriptor import DateRangeAggregatorDescriptor
from base_dash_app.virtual_objects.timeseries.time_series import AbstractTimeSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint

TSDP_DASH_RELOAD_INTERVAL_ID = "STS_DASH_RELOAD_INTERVAL_ID"

TS_DASH_WRAPPER_DOWNLOAD_ID = "STS_DASH_WRAPPER_DOWNLOAD_ID"

TS_DASH_DOWNLOAD_BTN_ID = "STS_DASH_DOWNLOAD_BTN_ID"

TS_DASH_RELOAD_BTN_ID = "simple-timeseries-dash-reload-btn-id"


class SimpleTimeSeriesDashboard(ComponentWithInternalCallback):
    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=TS_DASH_DOWNLOAD_BTN_ID,
                    input_property="n_clicks"
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=TS_DASH_RELOAD_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=TSDP_DASH_RELOAD_INTERVAL_ID,
                    input_property="n_intervals"
                ),
                states=[]
            )
        ]

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        instance: SimpleTimeSeriesDashboard
        instance.data_for_download = None

        if triggering_id.startswith(TS_DASH_DOWNLOAD_BTN_ID):
            instance.data_for_download = dcc.send_string(
                convert_dict_to_csv(
                    instance.tsdp_dtw.datatable.data,
                    [col["id"] for col in instance.tsdp_dtw.datatable.columns],
                    headers_override={col["id"]: col["name"] for col in instance.tsdp_dtw.datatable.columns}
                ),
                instance.tsdp_dtw.datatable.download_file_name
            )
        elif triggering_id.startswith(TS_DASH_RELOAD_BTN_ID):
            if instance.reload_data_function is None:
                raise PreventUpdate("Reload function was null.")

            def reload_tsdps(*args, **kwargs):
                if "async_container" in kwargs:
                    async_container = kwargs["async_container"]
                else:
                    async_container = AsyncWorkProgressContainer()

                async_container.start_time = datetime.datetime.now()
                async_container.execution_status = StatusesEnum.IN_PROGRESS
                async_container.progress = 0
                all_timeseries: List[AbstractTimeSeries] = instance.reload_data_function(async_container)
                async_container.progress = 50
                for series in all_timeseries:
                    async_container.progress = 50 + (40 / len(all_timeseries))
                    instance.set_data_for_timeseries(series, series.get_tsdps())

                instance.tsdp_dtw.datatable.set_data(instance.tsdp_dtw.generate_data_array())
                async_container.progress = 100
                instance.last_load_time = datetime.datetime.now()
                async_container.end_time = datetime.datetime.now()
                async_container.result = 1
                async_container.execution_status = StatusesEnum.SUCCESS
                time.sleep(0.5)

            if instance.get_service is not None:
                async_service: AsyncHandlerService = instance.get_service(AsyncHandlerService)

                def done_callback(*args, **kwargs):
                    instance.current_async_container = None

                instance.current_async_container = async_service.do_work(reload_tsdps, done_callback=done_callback)
            else:
                reload_tsdps()

        return [instance.__render_dash()]

    def __init__(
            self, title: str, base_date_range: DateRangeAggregatorDescriptor,
            reload_data_function: Callable[[Optional[AsyncWorkProgressContainer]], List[AbstractTimeSeries]],
            service_provider: Callable = None,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.data_for_download = None
        self.title: str = title

        self.time_series_wrappers: Dict[str, AbstractTimeSeriesWrapper] = {}
        self.last_load_time = None
        self.reload_data_function: Callable[[Optional[AsyncWorkProgressContainer]], List[AbstractTimeSeries]] \
            = reload_data_function
        self.get_service: Optional[Callable] = service_provider

        self.tsdp_dtw = TimeSeriesDataTableWrapper(
            title=title,
            start_date=base_date_range.start_date,
            end_date=base_date_range.end_date,
            interval_size=base_date_range.interval,
            aggregation_method=base_date_range.aggregation_method,
            hide_toolbar=True
            # reload_data_function=wrapper_generate_data(2, datetime.timedelta(hours=1)) # todo!
        )

        self.current_async_container: Optional[AsyncWorkProgressContainer] = None

        # todo: reload each time series individually?
        #   push reload function into time series wrapper?

    def add_timeseries(self, tsw: AbstractTimeSeriesWrapper):
        if tsw.get_unique_id() in self.time_series_wrappers:
            raise Exception("Cannot add duplicate time series!")

        self.time_series_wrappers[tsw.get_unique_id()] = tsw

        if tsw.get_show_in_datatable():
            self.tsdp_dtw.add_timeseries(tsw, format=tsw.get_column_format(), datatype=tsw.get_column_datatype())

    def overwrite_timeseries_wrapper(self, tsw: AbstractTimeSeriesWrapper):
        """
        todo: is this needed?
        :param tsw:
        :return:
        """
        if tsw.get_unique_id() not in self.time_series_wrappers:
            raise Exception("Cannot overwrite timeseries that wasn't aleady added!")  # todo: should just add?

        self.time_series_wrappers[tsw.get_unique_id()] = tsw

        if tsw.get_show_in_datatable():
            self.tsdp_dtw.overwrite_timeseries_data(tsw, tsw.get_tsdps())

    def set_data_for_timeseries(self, timeseries: AbstractTimeSeries, data: List[TimeSeriesDataPoint]):
        if timeseries.get_unique_id() not in self.time_series_wrappers:
            raise Exception(f"Cannot overwrite timeseries (id = {timeseries.get_unique_id()}) that wasn't aleady added!")  # todo: should just add?

        self.time_series_wrappers[timeseries.get_unique_id()].set_tsdps(data)

        if self.time_series_wrappers[timeseries.get_unique_id()].get_show_in_datatable():
            self.tsdp_dtw.overwrite_timeseries_data(timeseries, data)

    def __render_dash(self):
        stat_cards = [
            TsdpSparklineStatCard.init_from_descriptor(
                descriptor=sc_desc, series=tsw.get_tsdps()
            ).render()
            for uid, tsw in self.time_series_wrappers.items() for sc_desc in tsw.get_stat_card_descriptors()
        ]

        return html.Div(
            children=[
                html.H1(
                    self.title, style={"position": "relative", "float": "left", "maxWidth": "calc(100% - 400px)"}
                ),
                dcc.Interval(
                    id={"type": TSDP_DASH_RELOAD_INTERVAL_ID, "index": self._instance_id},
                    interval=1000,
                    n_intervals=0,
                    disabled=self.current_async_container is None or self.get_service is None
                ),
                construct_down_ref_btgrp(
                    reload_btn_id={"type": TS_DASH_RELOAD_BTN_ID, "index": self._instance_id},
                    download_btn_id={"type": TS_DASH_DOWNLOAD_BTN_ID, "index": self._instance_id},
                    last_load_time=self.last_load_time,
                    disable_reload_btn=self.reload_data_function is None,
                    disable_download_btn=self.last_load_time is None,
                    wrapper_style={"margin": "0"},
                    download_content_id={"type": TS_DASH_WRAPPER_DOWNLOAD_ID, "id": self._instance_id},
                    download_content=self.data_for_download,
                    reload_in_progress=self.current_async_container is not None,
                    reload_progress=self.current_async_container.progress
                        if self.current_async_container is not None else 0,
                ),
                html.Div(
                    children=stat_cards,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left",
                        "padding": "10px",
                        "width": "100%",
                        "minHeight": "350px",
                        "display": "none" if len(stat_cards) == 0 else ""
                    },
                ),
                self.tsdp_dtw.render()
            ],
        )

    def render(self, wrapper_style_override=None):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        return html.Div(
            children=self.__render_dash(),
            id={"type": SimpleTimeSeriesDashboard.get_wrapper_div_id(), "index": self._instance_id},
            style={**wrapper_style_override}
        )