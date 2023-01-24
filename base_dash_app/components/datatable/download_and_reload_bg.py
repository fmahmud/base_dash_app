import datetime

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.utils import date_utils


def construct_down_ref_btgrp(
    download_btn_id, reload_btn_id,
    last_load_time: datetime.datetime = None,
    date_format="%Y-%m-%d", time_format="%H:%M:%S",
    disable_download_btn=False, disable_reload_btn=False,
    other_buttons=None,
    wrapper_style=None
):
    if other_buttons is None:
        other_buttons = []

    if wrapper_style is None:
        wrapper_style = {}

    return html.Div(
        children=[
            dbc.ButtonGroup(
                children=[
                    dbc.Button(
                        [html.I(className="fa-solid fa-download")],
                        id=download_btn_id,
                        style={
                            "fontSize": "25px", "width": "65px",
                        },
                        disabled=disable_download_btn
                    ) if download_btn_id is not None else None,
                    dbc.Button(
                        [html.I(className="fa-solid fa-arrows-rotate")],
                        id=reload_btn_id,
                        style={
                            "fontSize": "25px", "width": "65px",
                        },
                        color="secondary",
                        disabled=disable_reload_btn
                    ),
                    *other_buttons
                ],
                style={"position": "relative", "float": "right", "clear": "right", "height": "50px"},
            ),
            html.H5(
                f"Last Loaded {date_utils.readable_time_since(last_load_time)} ago"
                if last_load_time is not None
                else "Never Loaded",
                style={
                    "position": "relative",
                    "float": "right",
                    "height": "100%",
                    "marginTop": "15px",
                    "margin-right": "20px",
                },
            )
        ],
        style={
            "position": "relative", "float": "right", "width": "450px", "marginTop": "20px", "marginBottom": "20px",
            **wrapper_style
        }
    )
