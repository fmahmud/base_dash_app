from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
import dash_bootstrap_components as dbc


class DBCTable(BaseComponent):
    def __init__(self, headers: List[str] = None, rows: List[List] = None):
        self.headers = headers
        self.rows = rows

    def render(self, *args, **kwargs):
        table_header = [
            html.Thead(html.Tr([html.Th(header) for header in self.headers]))
        ]

        rows = [
            html.Tr([html.Td(cell) for cell in row])
            for row in self.rows
        ]

        table_body = [html.Tbody(rows)]

        return dbc.Table(
            table_header + table_body,
            bordered=True,
            dark=True,
            hover=True,
            responsive=True,
            striped=True,
        )