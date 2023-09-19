import uuid
from abc import ABC, abstractmethod
from typing import Callable, List

import dash
from dash import ALL, MATCH, Output, dcc
from dash.exceptions import PreventUpdate

from base_dash_app.components.callback_utils.exceptions import ComponentInstanceNotFoundException
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.components.callback_utils.utils import get_state_values_for_input_from_args_list, invalid_n_clicks, \
    get_triggering_id_from_callback_context
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject


class BaseComponent(ABC):
    def __init__(self, *args, **kwargs):
        self.id = uuid.uuid4().hex

    @abstractmethod
    def render(self, *args, **kwargs):
        pass


class ComponentWithInternalCallback(BaseComponent, VirtualFrameworkObject, ABC):
    type_to_instances_map = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        VirtualFrameworkObject.__init__(self, *args, **kwargs)
        if type(self) not in ComponentWithInternalCallback.type_to_instances_map:
            ComponentWithInternalCallback.type_to_instances_map[type(self)] = {}

        self._instance_id = len(ComponentWithInternalCallback.type_to_instances_map[type(self)]) + 1

        ComponentWithInternalCallback.type_to_instances_map[type(self)][self._instance_id] = self

    @staticmethod
    @abstractmethod
    def get_input_to_states_map():
        pass

    @classmethod
    def get_wrapper_div_id(cls):
        return f"{cls.__name__}-wrapper-div-id"

    @classmethod
    def do_registrations(cls, register_callback_func):
        """
        method will be called by RuntimeApplication to allow each component class to register
        its callbacks at startup time. Each callback defined by the child component will
        have to be non-dynamic, and will be converted into a dynamic callback with the instance
        id as the index.
        """
        if not issubclass(cls, ComponentWithInternalCallback):
            raise Exception("Passed class should inherit ComponentWithInternalCallback.")

        input_to_states_map: List[InputToState] = cls.get_input_to_states_map()

        if any(its.input.is_dynamic for its in input_to_states_map):
            raise Exception("Internal callbacks cannot be dynamic.")

        for its in input_to_states_map:
            its.input.is_dynamic = True
            its.input.index = its.input.index or MATCH

            for state in its.states:
                state.is_dynamic = True
                if state.index is None:
                    state.index = MATCH

        if len(input_to_states_map) > 0:
            register_callback_func(
                output=[Output({"type": cls.get_wrapper_div_id(), "index": MATCH}, "children")],
                inputs=[its.input.get_as_input() for its in input_to_states_map],
                state=[state.get_as_state() for its in input_to_states_map for state in its.states],
                function=cls.__pre_handle_any_input,
                prevent_initial_call=True
            )

    def get_callback_state(self, input_id, args):
        input_to_states_map: List[InputToState] = type(self).get_input_to_states_map()

        return get_state_values_for_input_from_args_list(
            input_id=input_id,
            input_string_ids_map={
                input_to_state.input.get_string_id(): input_to_state
                for input_to_state in input_to_states_map
            },
            args_list=list(args[len(input_to_states_map):])
        )

    @classmethod
    def __pre_handle_any_input(cls, *args):
        """
        This function will be called when there is a callback with a positional parameter
        for each input and state defined in the input_to_state_map. Each positional parameter
        will be an array because all the callbacks are defined as dynamic.

        @param args:
        @return:
        """

        num_inputs = len(cls.get_input_to_states_map())

        # check if all inputs have an invalid state
        # todo: invert this check to "any(valid...)
        if all(invalid_n_clicks(i) for i in args[0:num_inputs]):
            raise PreventUpdate()

        # get triggering id
        triggering_id, index = get_triggering_id_from_callback_context(dash.callback_context)

        # get triggering instance
        # todo - decide if index should reuse IDs as they get destroyed or should instance IDs be always increasing
        if cls not in ComponentWithInternalCallback.type_to_instances_map:
            raise PreventUpdate()

        if (type(index) == int and index < 1) or triggering_id is None or triggering_id == ".":
            raise PreventUpdate()

        if index not in ComponentWithInternalCallback.type_to_instances_map[cls]:
            raise Exception(f"Instance ID {index} for class {cls} was not found!")

        triggering_instance = ComponentWithInternalCallback.type_to_instances_map[cls][index]

        # component class specific validation
        cls.validate_state_on_trigger(triggering_instance)

        if triggering_id is None:
            raise PreventUpdate()

        return cls.handle_any_input(
            *args, triggering_id=triggering_id, instance=triggering_instance
        )

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        raise PreventUpdate()

    @classmethod
    def validate_state_on_trigger(cls, instance):
        if type(instance) != cls:
            raise PreventUpdate(f"Instance was of type {type(instance)} instead of {cls}")

        return