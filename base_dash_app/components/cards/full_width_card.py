from base_dash_app.components.base_component import BaseComponent
from dash import html


class ThreeColumnCard(BaseComponent):
    def __init__(self):
        super().__init__()

    def render(self, column1_content, column2_content, column3_content, style_override=None):
        if style_override is None:
            style_override = {}

        column_style = {
            "width": "calc(33% - 20px)",
            "minWidth": "400px",
            "height": "100%",
            "float": "left",
            "position": "relative",
            "marginRight": "20px",
        }

        return html.Div(
            children=[
                html.Div(
                    children=column1_content,
                    style=column_style
                ),
                html.Div(
                    children=column2_content,
                    style=column_style
                ),
                html.Div(
                    children=column3_content,
                    style=column_style
                )
            ],
            className="card",
            style={
                "position": "relative", "float": "left",
                "width": "100%", "height": "300px", "padding": "20px",
                "flexDirection": "row",
                **style_override
            }
        )