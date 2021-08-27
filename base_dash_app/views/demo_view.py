import datetime
import re
from typing import Callable

from base_dash_app.components.lists.todo_list.todo_list import TodoList
from base_dash_app.models.task import Task
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView


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

    @staticmethod
    def raw_render(todo_list_component):
        return todo_list_component.render()

    def render(self, query_params):
        return DemoView.raw_render(self.todo_list_component)