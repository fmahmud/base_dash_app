from base_dash_app.components.base_component import BaseComponent
import dash_bootstrap_components as dbc


class NavBar(BaseComponent):
    def __init__(self, title: str, nav_items):
        self.nav_items = nav_items
        self.title = title if title is not None else ""

    def render(self):
        return dbc.NavbarSimple(
            children=self.nav_items,
            brand=self.title,
            color="primary",
            sticky="top",
            dark=True
        )
