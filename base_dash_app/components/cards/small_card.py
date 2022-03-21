
import dash_bootstrap_components as dbc
from base_dash_app.components.base_component import BaseComponent


class SmallCard(BaseComponent):
    def __init__(
            self, title, body,
            left_complication=None, right_complication=None,
            style=None, actions=None
    ):
        self.title = title
        self.body = body
        self.style = style if style is not None else {}
        self.style = self.style
        self.left_complication = left_complication
        self.right_complication = right_complication
        self.actions = actions if actions is not None else []

    def render(self, *args, **kwargs):
        card_children = []
        complication_width = 25
        max_body_width = \
            100 - (complication_width if self.left_complication is not None else 0) \
            - (complication_width if self.right_complication is not None else 0)

        complication_style = {
            "maxWidth": f"calc({complication_width}% - .5rem)",
            "width": f"calc({complication_width}% - .5rem)",
            "lineHeight": "6rem",
            "marginLeft": ".5rem"
        }

        if self.left_complication is not None:
            card_children.append(
                dbc.Col(self.left_complication, style=complication_style)
            )

        card_children.append(
            dbc.Col(
                dbc.CardBody(
                    [
                        self.title,
                        self.body
                    ]
                ),
                style={"maxWidth": f"{max_body_width}%", "width": f"{max_body_width}%"}
            ),
        )

        if self.right_complication is not None:
            card_children.append(
                dbc.Col(self.right_complication, style=complication_style)
            )

        return dbc.Card(
            children=[
                dbc.Row(card_children),
                dbc.Row(self.actions, style={"margin": "0 -5px"})
                if len(self.actions) > 0 else "",
            ],
            style=self.style
        )
