import datetime
import time
from typing import Dict, List, Callable, Optional

import dash_bootstrap_components as dbc
import dash_table
from dash import html
from dash.exceptions import PreventUpdate

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.datatable.download_and_reload_bg import construct_down_ref_btgrp
import dash_core_components as dcc

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncWorkProgressContainer, AsyncHandlerService
from base_dash_app.utils.file_utils import convert_dict_to_csv

DATATABLE_INTERVAL_ID = "DATATABLE_INTERVAL_ID"

RELOAD_DASH_BTN_ID = "RELOAD_DASH_BTN_ID"

DOWNLOAD_DATA_BTN_ID = "DOWNLOAD_DATATABLE_BTN_ID"

DATA_TABLE_WRAPPER_DOWNLOAD_ID = "data-table-wrapper-download-id"


class DataTableWrapper(ComponentWithInternalCallback):
    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        instance: DataTableWrapper
        instance.data_for_download = None

        if triggering_id.startswith(DOWNLOAD_DATA_BTN_ID):
            instance.data_for_download = dcc.send_string(
                convert_dict_to_csv(
                    instance.data,
                    [col["id"] for col in instance.columns],
                    headers_override={col["id"]: col["name"] for col in instance.columns}
                ),
                instance.download_file_name
            )
        elif triggering_id.startswith(RELOAD_DASH_BTN_ID):
            if instance.reload_data_function is None:
                raise PreventUpdate("Reload function was null.")

            def reload_and_set_data(*args, **kwargs):
                if "async_container" in kwargs:
                    async_container = kwargs["async_container"]
                else:
                    async_container = AsyncWorkProgressContainer()

                async_container.start()
                data = instance.reload_data_function(async_container=async_container)
                async_container.progress = 50
                instance.set_data(data)
                async_container.complete()
                time.sleep(0.5)

            if instance.get_service is not None:
                async_service: AsyncHandlerService = instance.get_service(AsyncHandlerService)

                def done_callback(*args, **kwargs):
                    instance.current_async_container = None

                instance.current_async_container = async_service.do_work(
                    reload_and_set_data, done_callback=done_callback
                )
            else:
                reload_and_set_data()

        return [instance.__render_data_table()]


    @classmethod
    def validate_state_on_trigger(cls, instance):
        if type(instance) != cls:
            raise PreventUpdate(f"Instance was of type {type(instance)} instead of {cls}")

        return

    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=DOWNLOAD_DATA_BTN_ID,
                    input_property="n_clicks"
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=RELOAD_DASH_BTN_ID,
                    input_property="n_clicks"
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=DATATABLE_INTERVAL_ID,
                    input_property="n_intervals"
                ),
                states=[]
            )
        ]

    def __init__(
            self, title: str,
            columns: list,
            reload_data_function: Callable = None,
            hide_toolbar=False,
            rows_per_page=500,
            service_provider: Callable = None,
            additional_buttons: List = None,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.title = title
        self.load_on_render: bool = False
        self.downloadable: bool = True
        self.hide_toolbar = hide_toolbar

        self.columns: List[Dict] = columns or []
        self.last_load_time = None

        self.data: List = []
        self.data_for_download = None
        self.sort_action = "native"
        self.filter_action = "native"
        self.download_file_name = f"{datetime.datetime.now()}-{title}.csv"

        self.reload_data_function = reload_data_function
        self.rows_per_page = rows_per_page

        self.get_service: Optional[Callable] = service_provider
        self.current_async_container: Optional[AsyncWorkProgressContainer] = None

        self.additional_buttons = additional_buttons or []

    def set_data(self, data):
        self.last_load_time = datetime.datetime.now()
        self.data = data

    def add_row(self, row):
        self.data.append(row)

    def __render_data_table(self):
        return html.Div(
            children=[
                dcc.Interval(
                    id={"type": DATATABLE_INTERVAL_ID, "index": self._instance_id},
                    interval=1000,
                    n_intervals=0,
                    disabled=self.current_async_container is None or self.get_service is None or self.hide_toolbar
                ),
                construct_down_ref_btgrp(
                    download_btn_id={
                        "type": DOWNLOAD_DATA_BTN_ID,
                        "index": self._instance_id,
                    },
                    reload_btn_id={"type": RELOAD_DASH_BTN_ID, "index": self._instance_id},
                    last_load_time=self.last_load_time,
                    disable_reload_btn=self.reload_data_function is None,
                    disable_download_btn=self.data is None or len(self.data) == 0,
                    download_content_id={
                        "type": DATA_TABLE_WRAPPER_DOWNLOAD_ID,
                        "id": self._instance_id
                    },
                    download_content=self.data_for_download,
                    reload_in_progress=self.current_async_container is not None,
                    reload_progress=self.current_async_container.progress
                        if self.current_async_container is not None else 0,
                    wrapper_style={"display": "none"} if self.hide_toolbar else None,
                    other_buttons=self.additional_buttons,
                ),
                dash_table.DataTable(
                    style_header={
                        "whiteSpace": "normal",
                        "height": "auto",
                    },
                    id=f"data-table-wrapper-{self._instance_id}",
                    data=self.data,
                    columns=self.columns,
                    style_table={
                        "position": "relative",
                        "float": "left",
                        "width": "100%",
                        "marginBottom": "20px",
                    },
                    sort_action=self.sort_action,
                    filter_action=self.filter_action,
                    page_size=self.rows_per_page
                ),
            ]
        )

    def render(self, wrapper_style_override=None):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        return html.Div(
            children=self.__render_data_table(),
            id={"type": DataTableWrapper.get_wrapper_div_id(), "index": self._instance_id},
            style={**wrapper_style_override}
        )