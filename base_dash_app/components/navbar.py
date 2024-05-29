from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
import dash_bootstrap_components as dbc

from base_dash_app.utils import utils


class NavDefinition:
    def __init__(self, label, url: str):
        self.label = label
        self.url: str = url

    def render(self, inner_style_override=None):
        return dbc.NavItem(
            dbc.NavLink(
                self.label,
                href=self.url,
                external_link=False,
                style=inner_style_override if inner_style_override is not None else {}
            ),
            style={"fontSize": "16px"}
        )


class NavGroup:
    def __init__(self, group_label: str, navs: List[NavDefinition] = None):
        self.group_label: str = group_label
        self.navs: List[NavDefinition] = navs if navs is not None else []

    def add_nav(self, nav: NavDefinition):
        self.navs.append(nav)

    def render(self):
        return dbc.DropdownMenu(
            [dbc.DropdownMenuItem(nav.render({"color": "black"})) for nav in self.navs],
            label=self.group_label,
            nav=True,
            align_end=True,
        )


class NavBar(BaseComponent):
    def __init__(
        self, title: str, nav_items, *args,
        nav_groups: List[NavGroup] = None, extra_components=None,
        show_cpu_usage=False, show_memory_usage=False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.nav_items = nav_items
        self.title = title if title is not None else ""
        self.nav_groups = nav_groups if nav_groups is not None else []
        self.extra_components = extra_components if extra_components is not None else []
        self.show_cpu_usage = show_cpu_usage
        self.show_memory_usage = show_memory_usage
        self.memory_consumption_bar = html.Div(
            children=[
                html.Div(
                    "0 MB",
                    id="nav-bar-memory-consumption-label",
                    style={
                        "marginRight": "10px", "color": "white", "fontSize": "14px",
                        "position": "relative", "float": "left", "width": "65px"
                    },
                ),
                dbc.Progress(
                    max=1000,
                    value=0,
                    style={
                        "height": "18px", "width": "200px",
                        "position": "relative", "float": "left"
                    },
                    hide_label=True,
                    id="nav-bar-memory-consumption-bar"
                ),
            ],
            style={
                "position": "relative", "float": "left",
                "width": "300px", "height": "20px",
                "display": "none" if not self.show_memory_usage else None
            }
        )

        self.cpu_usage_bar = html.Div(
            children=[
                html.Div(
                    "0.0%",
                    id="nav-bar-cpu-usage-label",
                    style={
                        "marginRight": "10px", "color": "white", "fontSize": "14px",
                        "position": "relative", "float": "left", "width": "65px"
                    },
                ),
                dbc.Progress(
                    max=100,
                    value=0,
                    style={
                        "height": "18px", "width": "200px",
                        "position": "relative", "float": "left"
                    },
                    hide_label=True,
                    id="nav-bar-cpu-usage-bar"
                ),
            ],
            style={
                "position": "relative", "float": "left",
                "width": "300px", "height": "20px", "marginTop": "5px",
                "display": "none" if not self.show_cpu_usage else None
            }
        )

    def render(self):
        return dbc.NavbarSimple(
            children=(
                [
                    html.Div(
                        children=[
                            self.memory_consumption_bar,
                            self.cpu_usage_bar
                        ],
                        style={"height": "50px", "width": "300px", "paddingTop": "3px"}
                    )
                ]
                + self.nav_items
                + [ng.render() for ng in self.nav_groups]
                + self.extra_components
            ),
            brand=self.title,
            color="primary",
            sticky="top",
            dark=True,
            style={"boxShadow": "rgb(0 0 0 / 24%) 0px 5px 5px -1px", "paddingRight": "20px", "paddingLeft": "20px"},
            fluid=True
        )
