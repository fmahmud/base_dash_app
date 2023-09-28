import datetime

import dash_bootstrap_components as dbc
from dash import html, dcc

from base_dash_app.utils import date_utils


def construct_down_ref_btgrp(
    download_btn_id, reload_btn_id,
    last_load_time: datetime.datetime = None,
    date_format="%Y-%m-%d", time_format="%H:%M:%S",
    disable_download_btn=False,
    disable_reload_btn=False,
    other_buttons=None,
    wrapper_style=None,
    download_content=None,
    download_content_id=None,
    reload_in_progress=False,
    reload_progress=0,
    hide_download_button=False,
    right_align=True,
):
    if other_buttons is None:
        other_buttons = []

    if wrapper_style is None:
        wrapper_style = {}

    spin_animation = {}
    if reload_in_progress:
        spin_animation = {
            "animation": "spin 1s linear infinite",
            "WebkitAnimation": "spin 1s linear infinite",
        }

    float_direction = "right" if right_align else "left"

    return html.Div(
        children=[
            dcc.Download(data=download_content, id=download_content_id) if download_content_id is not None else None,
            dbc.ButtonGroup(
                children=[
                    dbc.Button(
                        [html.I(className="fa-solid fa-download")],
                        id=download_btn_id,
                        style={
                            "fontSize": "25px", "width": "65px",
                            "display": "none" if hide_download_button else None
                        },
                        disabled=disable_download_btn or reload_in_progress
                    ) if download_btn_id is not None else None,
                    dbc.Button(
                        [html.I(className="fa-solid fa-arrows-rotate", style=spin_animation)],
                        id=reload_btn_id,
                        style={
                            "fontSize": "25px", "width": "65px",
                        },
                        color="secondary",
                        disabled=disable_reload_btn or reload_in_progress
                    ),
                    *other_buttons
                ],
                style={"position": "relative", "float": float_direction, "clear": float_direction, "height": "50px"},
            ),
            html.H5(
                f"Last Loaded {date_utils.readable_time_since(last_load_time)} ago"
                if last_load_time is not None
                else "Never Loaded",
                style={
                    "position": "relative",
                    "float": float_direction,
                    "height": "100%",
                    "marginTop": "15px",
                    f"margin{float_direction.title()}": "20px",
                },
            ) if not reload_in_progress else
            dbc.Progress(
                value=reload_progress,
                label=f"{reload_progress:.0f}%",
                color="black",
                animated=True,
                striped=True,
                style={
                    "position": "relative",
                    "float": float_direction,
                    "marginTop": "15px",
                    f"margin{float_direction.title()}": "20px",
                    "width": "300px",
                    "height": "20px"
                }
            ),
        ],
        style={
            "position": "relative", "float": float_direction,
            "marginTop": "20px", "marginBottom": "20px",
            "width": "fit-content",
            **wrapper_style
        }
    )
