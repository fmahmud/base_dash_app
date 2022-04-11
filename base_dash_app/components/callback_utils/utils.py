from typing import List, Dict

from base_dash_app.components.callback_utils.mappers import StateMapping, InputToState


def is_empty_or_none(s):
    if s is None or s == "":
        return True
    return False


def invalid_n_clicks(n_clicks):
    if n_clicks in [[None], [], None, 0]:
        return True

    if type(n_clicks) == list:
        return all(n in [[None], [], None, 0] for n in n_clicks)


def get_triggering_id_from_callback_context(callback_context):
    import json
    triggering_id = ""
    if len(callback_context.triggered) == 1 and "prop_id" in callback_context.triggered[0]:
        triggering_id = callback_context.triggered[0]["prop_id"]

    if triggering_id.startswith("{"):
        triggering_id = triggering_id.split("}.")[0] + "}"
        id_as_json = json.loads(triggering_id)
        if "type" in id_as_json and "index" in id_as_json:
            return id_as_json["type"], id_as_json["index"]
        else:
            # invalid json payload as triggering id:
            raise Exception("Invalid json payload as triggering id %s" % triggering_id)

    return triggering_id, 0


def get_state_values_for_input_from_args_list(input_id, input_string_ids_map: Dict[str, InputToState], args_list):
    if input_id in input_string_ids_map:
        offset = 0
        for str_id, its in input_string_ids_map.items():
            if str_id == input_id:
                break

            offset += len(its.states)

        state_to_value_map = {}
        states_list: List[StateMapping] = input_string_ids_map[input_id].states
        for state in states_list:
            state_to_value_map[state.get_string_id()] = args_list[offset + states_list.index(state)]

        return state_to_value_map
    else:
        return None