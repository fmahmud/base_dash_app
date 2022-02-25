from abc import ABC, abstractmethod
from typing import Pattern, Callable, Optional, List

import dash
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.callback_utils.utils import invalid_n_clicks, get_triggering_id_from_callback_context
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.utils.db_utils import DbManager


class BaseView(BaseComponent, ABC):
    VIEWS = []

    def __init__(
            self, title: str, url_regex: Pattern[str], register_callback_func: Callable,
             dbm: Optional[DbManager] = None, nav_url: str = "", show_in_navbar: bool = True,
             service_provider: Callable = None, input_to_states_map: List[InputToState] = None
    ):
        self.title: str = title
        self.url_regex = url_regex
        self.path_params = {}
        self.nav_url = nav_url
        self.show_in_navbar = show_in_navbar
        self.register_callback_func = register_callback_func
        self.get_service = service_provider
        self.dbm: Optional[DbManager] = dbm
        self.input_to_states_map: List[InputToState] = input_to_states_map if input_to_states_map else []
        self.input_string_ids_map = {its.get_input_string_id(): its for its in self.input_to_states_map}

        self.wrapper_div_id: str = f"{self.title.lower().replace(' ', '-')}-wrapper-div-id"

        if len(self.input_to_states_map) > 0:
            register_callback_func(
                output=[Output(self.wrapper_div_id, "children")],
                inputs=[its.input.get_as_input() for its in self.input_to_states_map],
                state=[state.get_as_state() for its in self.input_to_states_map for state in its.states],
                function=self._pre_handle_any_input.__get__(self, self.__class__)
            )

        if self not in BaseView.VIEWS:
            BaseView.VIEWS.append(self)

    def _pre_handle_any_input(self, *args):
        if all(invalid_n_clicks(i) for i in args[0:len(self.input_to_states_map)]):
            raise PreventUpdate()

        # view specific validation
        self.validate_state_on_trigger()

        # get triggering id
        triggering_id, index = get_triggering_id_from_callback_context(dash.callback_context)

        if triggering_id is None:
            raise PreventUpdate()

        return self.handle_any_input(
            *args, triggering_id=triggering_id, index=index
        )

    def handle_any_input(self, *args, triggering_id, index):
        raise PreventUpdate()

    def validate_state_on_trigger(self):
        raise PreventUpdate()

    # todo: move path params out of here. make it a return variable and have it sent to render function
    def matches(self, target_url: str):
        self.path_params = {}
        match_result = self.url_regex.match(target_url)
        if match_result is None:
            return False
        self.path_params = match_result.groupdict()
        return True

    @staticmethod
    @abstractmethod
    def raw_render(*args, **kwargs):
        pass

    # @staticmethod
    # def get_full_page_inputs():
    #     return []

