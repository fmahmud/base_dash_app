import datetime

import dash_bootstrap_components as dbc
from dash import html


def construct_down_ref_btgrp(
    download_btn_id, reload_btn_id,
    last_load_time: datetime.datetime = None,
    date_format="%Y-%m-%d", time_format="%H:%M:%S",
    disable_download_btn=False, disable_reload_btn=False
):
    return html.Div(
        children=[
            dbc.ButtonGroup(
                children=[
                    dbc.Button(
                        [html.I(className="fa-solid fa-download")],
                        id=download_btn_id,
                        style={
                            "margin": "20px 0", "fontSize": "25px", "width": "65px",
                        },
                        disabled=disable_download_btn
                    ),
                    dbc.Button(
                        [html.I(className="fa-solid fa-arrows-rotate")],
                        id=reload_btn_id,
                        style={
                            "margin": "20px 0", "fontSize": "25px", "width": "65px",
                        },
                        color="secondary",
                        disabled=disable_reload_btn
                    ),
                ],
                style={"position": "relative", "float": "right", "clear": "right"},
            ),
            html.H5(
                f"Last Loaded at: {last_load_time.strftime(date_format + ' ' + time_format)}",
                style={
                    "position": "relative",
                    "float": "right",
                    "height": "100%",
                    "marginTop": "35px",
                    "margin-right": "20px",
                },
            )
            if last_load_time is not None
            else None,
        ]
    )
