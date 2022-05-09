from typing import Dict, List

from dash import html

from base_dash_app.components.data_visualization import ratio_bar
from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.data_visualization.ratio_bar import StatusToCount
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.utils import utils
from base_dash_app.virtual_objects.interfaces.detailable import Detailable
import dash_bootstrap_components as dbc

banner_element_styles = {
    "marginLeft": "14px", "position": "relative", "float": "left", "fontSize": "14px", "height": "55px",
    "lineHeight": "55px"
}

# todo: make alternative to detailable which has same features but doesn't rely on details - maybe dbc.Card?


class DetailTextItem(BaseComponent):
    def __init__(self, text, style: Dict[str, str]):
        self.text = text
        self.style: Dict[str, str] = utils.apply(banner_element_styles, style)

    def render(self, *args, **kwargs):
        return html.Div(
            children=self.text,
            style=self.style
        )


def render_summary_inner_div_from_detailable(detailable: Detailable):
    status_to_counts: List[StatusToCount] = [
        StatusToCount("Success", StatusesEnum.SUCCESS, detailable.get_successes()),
        StatusToCount("Warning", StatusesEnum.WARNING, detailable.get_warnings()),
        StatusToCount("In Progress", StatusesEnum.IN_PROGRESS, detailable.get_in_progress()),
        StatusToCount("Failed", StatusesEnum.FAILURE, detailable.get_failures()),
        StatusToCount("Pending", StatusesEnum.PENDING, detailable.get_num_pending()),
    ]

    return render_summary_inner_div(
        texts=detailable.get_text_items(),
        show_ratio_bar=detailable.show_ratio_bar(),
        status_to_count_list=status_to_counts
    )


def render_summary_inner_div(texts: List[DetailTextItem], successes: int = 0, failures: int = 0, warnings: int = 0,
                             show_ratio_bar=True, *, status_to_count_list: List[StatusToCount] = None,
                             wrapper_style_override: Dict[str, str] = None):
    rendered_ratio_bar = ''
    max_width = "calc(100% - 18px)"
    if show_ratio_bar:
        max_width = "calc(100% - 315px)"
        if status_to_count_list is not None:
            rendered_ratio_bar = ratio_bar.render_from_stc_list(status_to_count_list)
        else:
            rendered_ratio_bar = ratio_bar.render(successes=successes, failures=failures, warns=warnings)

    return html.Div(
        children=[
            html.Div(
                children=[dti.render() for dti in texts],
                style={"position": "relative", "float": "left", "width": max_width}
            ),
            html.Div(
                children=rendered_ratio_bar,
                style=utils.apply(
                    banner_element_styles, {"width": '300px', "position": "relative", "float": "right"}
                )
            ) if rendered_ratio_bar != '' else ''
        ],
        style={"width": "calc(100% - 18px)", "height": "100%", "display": "inline", "position": "relative", "float": "left"},
        className="display_child_on_hover_only"
    )


def render_from_detailable(d: Detailable, num_rows: int = 1):
    wrapper_div_id = d.get_wrapper_element_id()
    summary_div_id = d.get_summary_div_id()

    global render_count
    render_count += 1

    if summary_div_id is None:
        summary_div_id = "details-summary-div-%i" % render_count

    if wrapper_div_id is None:
        wrapper_div_id = "details-wrapper-div-%i" % render_count

    height = num_rows * 56
    if d.get_height_override() is not None:
        height = d.get_height_override()

    children = [
        html.Summary(
            children=[
                render_summary_inner_div_from_detailable(d),
            ], style={"width": "100%", "height": "%ipx" % height},
            id=summary_div_id
        )
    ]

    if d.has_details():
        children.append(
            html.Div(d.get_detail_component(), style={"width": "100%", "height": "100%", "display": "fixed"})
        )

    style = {
        "width": "100%",
        "minHeight": "%ipx" % height,
        "position": "relative",
        "float": "left",
        "border": "1px solid rgba(0, 0, 0, 0.2)",
        # "borderRadius": "4px",
        "marginBottom": "10px",
        # "boxShadow": "0 0px 2px 0 rgba(0, 0, 0, 0.3)",
        "WebkitTouchCallout": "none",
        # "userSelect": "none",
        "lineHeight": "%ipx" % height,
    }

    if d.has_details():
        return  html.Details(
            children=children,
            style=style,
            id=wrapper_div_id
        )
    else:
        return dbc.Card(
            children=children,
            style=style,
            body=True,
            id=wrapper_div_id
        )


render_count = 0


def render(successes: int, failures: int, warnings: int,
           details_component, texts: List[DetailTextItem], show_ratio_bar=True, num_rows: int = 2,
           *,
           state_to_count_list: List[StatusToCount] = None, summary_div_id=None, has_details=True):
    """
    deprecated. Use render_from_detailable instead.
    """

    if summary_div_id is None:
        global render_count
        render_count += 1
        summary_div_id = "details-summary-div-%i" % render_count

    height = num_rows * 55

    if has_details:
        details = html.Details(
            children=[
                html.Summary(
                    children=[
                        render_summary_inner_div(texts, successes, failures, warnings, show_ratio_bar),
                    ], style={"width": "100%", "height": "%ipx" % height},
                    id=summary_div_id
                ),
                html.Div(details_component, style={"width": "100%", "height": "100%", "display": "fixed"})
            ],
            style={
                "width": "100%",
                "minHeight": "%ipx" % height,
                "position": "relative",
                "float": "left",
                "border": "1px solid rgba(0, 0, 0, 0.2)",
                # "borderRadius": "4px",
                "marginBottom": "10px",
                # "boxShadow": "0 0px 2px 0 rgba(0, 0, 0, 0.3)",
                "WebkitTouchCallout": "none",
                # "userSelect": "none",
                "lineHeight": "%ipx" % height,
            }
        )
    else:
        details = dbc.Card(
            children=[
                html.Summary(
                    children=[
                        render_summary_inner_div(texts, successes, failures, warnings, show_ratio_bar),
                    ], style={"width": "100%", "height": "%ipx" % height},
                    id=summary_div_id
                ),
            ],
            body=True,
            style={
                "width": "100%",
                "minHeight": "%ipx" % height,
                "position": "relative",
                "float": "left",
                "border": "1px solid rgba(0, 0, 0, 0.2)",
                # "borderRadius": "4px",
                "marginBottom": "10px",
                # "boxShadow": "0 0px 2px 0 rgba(0, 0, 0, 0.3)",
                "WebkitTouchCallout": "none",
                # "userSelect": "none",
                "lineHeight": "%ipx" % height,
            }
        )

    return details
