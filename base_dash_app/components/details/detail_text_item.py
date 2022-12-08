from typing import Dict

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.utils import utils


class DetailTextItem(BaseComponent):
    def __init__(self, text, style: Dict[str, str]):
        self.text = text
        self.style: Dict[str, str] = utils.apply(banner_element_styles, style)

    def render(self, *args, **kwargs):
        return html.Div(
            children=self.text,
            style=self.style
        )


banner_element_styles = {
    "marginLeft": "14px", "position": "relative", "float": "left", "fontSize": "14px", "height": "55px",
    "lineHeight": "55px"
}
