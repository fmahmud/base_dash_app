import dash_bootstrap_components as dbc


class InfoCard:
    """
    A card that can render any amount of content in the body.
    """

    def __init__(self):
        self.width: int = 400
        self.content = []

    def set_content(self, content):
        self.content = content
        return self

    def add_content(self, value):
        self.content.append(value)
        return self

    def set_width(self, width):
        self.width = width
        return self

    def render(self, style_override=None):
        if style_override is None:
            style_override = {}

        return dbc.Card(
            children=dbc.CardBody(
                children=self.content
            ),
            style={
                "position": "relative",
                "float": "left",
                "width": f"{self.width}px",
                "marginRight": "10px",
                "marginBottom": "10px",
                "padding": "0px",
                **style_override,
            },
            className="display_child_on_hover_only"
        )
