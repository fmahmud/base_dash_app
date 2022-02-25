from typing import List

from dash.dependencies import ALL, _Wildcard, State, Input


class StateMapping:
    def __init__(self, state_id, state_property, *, is_dynamic=False, index=ALL):
        self._state_id = state_id
        self.state_property = state_property
        self.is_dynamic = is_dynamic
        self.index: _Wildcard = index

    def get_id(self):
        if self.is_dynamic:
            return {'type': self._state_id, 'index': self.index}
        return self._state_id

    def get_as_state(self):
        return State(self.get_id(), self.state_property)

    def get_string_id(self):
        return self._state_id

    def __hash__(self):
        return hash(f"{self._state_id}-{self.state_property}-{str(self.is_dynamic)}-{str(self.index)}")


class InputMapping:
    def __init__(self, input_id, input_property, *, is_dynamic=False, index=ALL):
        self._input_id = input_id
        self.input_property = input_property
        self.is_dynamic = is_dynamic
        self.index: _Wildcard = index

    def get_string_id(self):
        return self._input_id

    def get_id(self):
        if self.is_dynamic:
            return {'type': self._input_id, 'index': self.index}
        return self._input_id

    def get_as_input(self):
        return Input(self.get_id(), self.input_property)

    def __hash__(self):
        return hash(f"{self._input_id}-{self.input_property}-{str(self.is_dynamic)}-{str(self.index)}")


class InputToState:
    def __init__(self, input_mapping: InputMapping, states: List[StateMapping]):
        self.input = input_mapping
        self.states: List[StateMapping] = states

    def get_input_string_id(self):
        return self.input.get_string_id()