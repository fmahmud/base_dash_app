import datetime
import re
from typing import Callable

from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

from base_dash_app.components.data_visualization import ratio_bar
from base_dash_app.components.data_visualization.ratio_bar import StatusToCount
from base_dash_app.components.details import details
from base_dash_app.components.details.details import DetailTextItem
from base_dash_app.components.lists.todo_list.todo_list import TodoList
from base_dash_app.enums.status_colors import StatusColors
from base_dash_app.models.task import Task
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView
import dash_html_components as html
import dash_bootstrap_components as dbc
import finnhub


SEARCH_BAR_ID = "search-bar-id"

SEARCH_BUTTON_ID = "search-button-id"

SEARCH_RESULT_DIV_ID = "search-result-div-id"


class DemoView(BaseView):
    def __init__(self, register_callback_func: Callable, dbm: DbManager, service_provider: Callable):
        super().__init__(
            "Demo View", re.compile("^/demo$"), register_callback_func,
            show_in_navbar=True, nav_url="/demo", service_provider=service_provider, dbm=dbm
        )
        self.todo_list_component = TodoList(
            register_callback_func,
            [
                Task("Item 1", "Do item 1 really well."),
                Task("Item 2", "Do item 2 really well."),
                Task("Item 3", "Do item 2 really well."),
            ]
        )

        self.watchlist = []
        self.finnhub_client = finnhub.Client(api_key="c7o457qad3idf06mmdc0")

        register_callback_func(
            output=Output(SEARCH_RESULT_DIV_ID, "children"),
            inputs=[Input(SEARCH_BUTTON_ID, "n_clicks")],
            state=[State(SEARCH_BAR_ID, "value")],
            function=self.handle_search.__get__(self, self.__class__)
        )

    def handle_search(self, n_clicks, search_value):
        if n_clicks == 0 or n_clicks is None:
            raise PreventUpdate()

        if search_value is None or search_value == '':
            raise PreventUpdate()

        stock_quote = self.finnhub_client.quote(search_value)
        if "c" in stock_quote and "o" in stock_quote:
            stock_quote['symbol'] = search_value
            self.watchlist.append(stock_quote)

        return DemoView.render_watchlist(self.watchlist)

    @staticmethod
    def render_watchlist(watchlist):
        base_style = {"position": "relative", "float": "left", "minWidth": "100px", "maxWidth": "300px", "marginRight": "10px"}
        return [
            dbc.Card(
                children=[
                    html.Div(children=stock['symbol'], style=base_style),
                    html.Div(children="C: %f" % stock['c'], style=base_style),
                    html.Div(children="O: %f" % stock['o'], style=base_style),
                    html.Div(children="H: %f" % stock['h'], style=base_style),
                    html.Div(children="L: %f" % stock['l'], style=base_style),
                    html.Div(children="PC: %f" % stock['pc'], style=base_style),
                ],
                body=True,
                style={"flexDirection": "row", "background": "red" if stock["c"] < stock["o"] else "green"}
            )
            for stock in watchlist
        ]

    @staticmethod
    def raw_render(watchlist):
        # return todo_list_component.render()

        search_bar = dbc.Row(
            [
                dbc.Input(type="search", placeholder="Search",
                          id=SEARCH_BAR_ID,
                          style={"width": "1000px", "height": "50px", "fontSize": "24px", "padding": "10px"}),
                dbc.Button(
                    "Search", color="primary", className="ms-2", n_clicks=0,
                    id=SEARCH_BUTTON_ID,
                    style={"maxWidth": "230px", "height": "50px"}
                ),
            ],
            className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
            align="center",
        )

        return html.Div(
            children=[
                search_bar,
                html.Div(children=[], id=SEARCH_RESULT_DIV_ID, style={"marginTop": "40px"}),
                ratio_bar.render_from_stc_list([
                    StatusToCount(state_name="A", count=5, color=StatusColors.PENDING),
                    StatusToCount(state_name="A", count=5, color=StatusColors.IN_PROGRESS)
                ])
            ],
            style={"maxWidth": "1280px", "margin": "0 auto", "padding": "20px"}
        )

    def render(self, query_params):
        return DemoView.raw_render(self.watchlist)