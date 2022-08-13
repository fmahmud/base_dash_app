import datetime
from typing import Callable, List, Dict

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.models.task import Task

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

