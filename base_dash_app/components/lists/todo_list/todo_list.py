import datetime
from enum import Enum
from typing import Callable, List, Dict

from dash.dependencies import Output, Input, ALL, MATCH, State
from dash.exceptions import PreventUpdate

from base_dash_app.components.base_component import BaseComponent
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.models.task import Task
from base_dash_app.enums.todo_status_enum import TodoStatusEnum
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.nameable import Nameable

nonce = 0


class TodoList(BaseComponent):
    def __init__(self, register_callback_func: Callable, items: List[Task]):
        global nonce
        self.nonce = nonce
        nonce += 1

        self.register_callback_func = register_callback_func

        self.__items: Dict[int, Task] = {t.id: t for t in items}

        self.task_group_list: List[TaskGroup] = [
            TaskGroup(id=1, name="Test Group", repeat_period=7 * 24 * 60 * 60,
                      due_date=datetime.datetime.now() + datetime.timedelta(days=5))
        ]

    def render(self):
        return html.Div([
            tg.render() for tg in self.task_group_list
        ])

