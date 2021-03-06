from typing import List

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.enums.status_colors import StatusesEnum

ratio_bar_id = 0


def render_from_stc_list(status_to_count_list: List['StatusToCount']):
    global ratio_bar_id
    ratio_bar_id += 1
    total = sum(stc.count for stc in status_to_count_list)

    if total == 0:
        tooltip_value = "No Data"
        total = 1
    else:
        tooltip_value = ", ".join("%i %s" % (stc.count, stc.name) for stc in status_to_count_list if stc.count > 0)

    return html.Div(children=[
        dbc.Progress([
                dbc.Progress(value=100 * stc.count / total, color=stc.color, bar=True)
                for stc in status_to_count_list
            ],
            style={"marginTop": "20px", "marginRight": "20px"},
            id="ratio_bar_id_" + str(ratio_bar_id)
        ),
        dbc.Tooltip(tooltip_value, target="ratio_bar_id_" + str(ratio_bar_id))
    ], id="ratio_div_" + str(ratio_bar_id))


def render(successes, failures, warns=0, in_progress=0, style_override=None):
    if style_override is None:
        style_override = {}

    global ratio_bar_id
    ratio_bar_id += 1
    total = successes + failures + warns + in_progress
    if total == 0:
        tooltip_value = "No Data"
        total = 1
    else:
        tooltip_value = ""
        "" + str(warns) + " draws, " + str(failures) + " losses"

        if successes > 0:
            tooltip_value += str(successes)

        if warns > 0:
            if tooltip_value != "":
                tooltip_value += "/"

            tooltip_value += str(warns)

        if failures > 0:
            if tooltip_value != "":
                tooltip_value += "/"

            tooltip_value += str(failures)

        if in_progress > 0:
            if tooltip_value != "":
                tooltip_value += "/"

            tooltip_value += str(in_progress)

    return html.Div(children=[
        dbc.Progress(
            [
                dbc.Progress(value=100 * successes / total, color="success", bar=True),
                dbc.Progress(value=100 * warns / total, color="warning", bar=True),
                dbc.Progress(value=100 * failures / total, color="danger", bar=True),
                dbc.Progress(value=100 * in_progress / total, color="info", bar=True),
            ],
            style={**{"marginTop": "20px", "marginRight": "20px"}, **style_override},
            id="ratio_bar_id_" + str(ratio_bar_id)
        ),
        dbc.Tooltip(tooltip_value, target="ratio_bar_id_" + str(ratio_bar_id))
    ], id="ratio_div_"+str(ratio_bar_id))


class StatusToCount:
    def __init__(self, state_name: str, color: StatusesEnum, count: int):
        self.name: str = state_name
        self.color: str = color.value.bootstrap_alt
        self.count: int = count
