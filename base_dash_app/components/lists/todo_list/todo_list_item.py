import datetime
from typing import List, Dict

from dash import html
from dash.dependencies import Output, MATCH, Input, State
from dash.exceptions import PreventUpdate

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.details import details
from base_dash_app.components.details.detail_text_item import DetailTextItem
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.enums.task_repeat_period_enum import TaskRepeatPeriodEnum
from base_dash_app.enums.todo_status_enum import TodoStatusEnum
from base_dash_app.models.task import Task
from base_dash_app.virtual_objects.interfaces.detailable import Detailable
from base_dash_app.virtual_objects.interfaces.nameable import Nameable

import dash_bootstrap_components as dbc
import dash_core_components as dcc

task_id = 0


class TaskGroup(Detailable, Nameable, BaseComponent):
    def get_height_override(self):
        pass

    TASK_GROUP_LIST_ID = 'task-group-list-id'

    TASK_GROUP_WRAPPER_DIV_ID = 'task-group-wrapper-div'
    TASK_GROUP_SUMMARY_DIV_ID = 'task-group-summary-div'
    TASK_GROUP_DUE_DATE_PICKER_ID = 'task-group-due-date-picker'
    TASK_SUMMARY_DIV_ID = 'task-summary-div-id'

    ADD_TASK_BTN_ID = 'btn-add-task-to-group'
    NEW_TASK_INPUT_ID = 'new-task-input'
    NEW_TASK_IS_REPEATABLE_INPUT_ID = 'new-task-is-repeatable-input-id'
    NEW_TASK_REPEATS_DROPDOWN_ID = 'new-task-repeats-input-id'

    instance_map: Dict[int, 'TaskGroup'] = {}

    def __init__(self, id: int, name: str, due_date: datetime.datetime, repeat_period: int = 0):
        self.id: int = id
        self.name: str = name
        self.tasks: List[Task] = []
        self.due_date: datetime.datetime = due_date
        self.repeat_period: int = repeat_period

        TaskGroup.instance_map[self.id] = self

    def get_text_items(self) -> List[DetailTextItem]:
        text_items = []
        text_items.append(DetailTextItem(self.name, {"fontSize": "22px"}))

        now = datetime.datetime.now()
        days_left = (self.due_date - now).days
        style = {}
        if days_left <= 2:
            style["color"] = StatusesEnum.WARNING.value
        if days_left < 1:
            style["color"] = StatusesEnum.FAILURE.value
        text_items.append(DetailTextItem("%i days left" % days_left, style))

        text_items.append(DetailTextItem("Num Tasks: %i" % len(self.tasks), {}))

        return text_items

    def render(self):
        return details.render_from_detailable(self)

    def get_summary_div_id(self):
        return {'type': TaskGroup.TASK_GROUP_SUMMARY_DIV_ID, 'index': self.id}

    def get_wrapper_element_id(self):
        return {'type': TaskGroup.TASK_GROUP_WRAPPER_DIV_ID, 'index': self.id}

    def get_name(self):
        return self.name

    def handle_add_task(self, task_name, due_date: datetime.datetime = None,
                        repeat_period: TaskRepeatPeriodEnum = TaskRepeatPeriodEnum.DOES_NOT_REPEAT):
        # todo: make add task function more robust with due dates and priority drop downs

        self.tasks.append(
            Task(
                task_group=self,
                task_name=task_name,
                first_due_date=due_date,
                repeat_period=repeat_period
            )
        )

        return self.render_task_list()

    def render_task_list(self):
        to_return = []
        for task in self.tasks:
            header_style = {
                "position": "relative", "width": "30%", "height": "100%", "float": "left", "padding": 10
            }

            lgi_style = {
                "height": 100
            }

            if task.task_status == TodoStatusEnum.DONE:
                header_style["textDecoration"] = "line-through"
                lgi_style["backgroundColor"] = TodoStatusEnum.DONE.get_color()

            to_return.append(
                html.Div(
                    children=[
                        details.render_summary_inner_div(
                            task.get_summary_components(), 0, 0, 0, False,
                            wrapper_style_override=lgi_style
                        )
                    ],
                    id={'type': TaskGroup.TASK_SUMMARY_DIV_ID, 'index': task.id}
                )
            )

        return dbc.ListGroup(to_return)

    def get_detail_component(self):
        detail_comp = html.Div(children=[
            dbc.InputGroup(
                children=[
                    dbc.InputGroupAddon(
                        dcc.DatePickerSingle(
                            id={'type': TaskGroup.TASK_GROUP_DUE_DATE_PICKER_ID, 'index': self.id},
                            min_date_allowed=datetime.datetime.now(),
                            max_date_allowed=datetime.datetime.now() + datetime.timedelta(days=365.25 * 16),
                            initial_visible_month=datetime.datetime.now(),
                            date=datetime.datetime.now() + datetime.timedelta(days=5),
                            day_size=50,
                        ),
                        addon_type="prepend",
                        style={"lineHeight": "38px", "height": "38px"}
                    ),
                    dbc.Input(
                        id={'type': TaskGroup.NEW_TASK_INPUT_ID, 'index': self.id},
                        placeholder="Make todo list...",
                    ),
                    dbc.InputGroupAddon(
                        dcc.Dropdown(
                            options=[
                                {'label': "%s" % p.summary, 'value': p.name}
                                for p in TaskRepeatPeriodEnum
                            ],
                            id={'type': TaskGroup.NEW_TASK_REPEATS_DROPDOWN_ID, 'index': self.id},
                            style={'width': '200px', 'height': '38px', 'borderRadius': '0', 'borderLeft': '0'},
                            placeholder='Repeats every...'
                        ),
                        style={'lineHeight': '30px'}
                    ),
                    dbc.InputGroupAddon(
                        dbc.Button(
                            html.I(className="fas fa-plus"),
                            id={'type': TaskGroup.ADD_TASK_BTN_ID, 'index': self.id}, n_clicks=0),
                        addon_type="append",
                        style={'height': '38px'}
                    ),
                ],
                style={"height": "38px"}
            ),
            html.Div(
                children=self.render_task_list() if len(self.tasks) > 0 else "No tasks yet.",
                id={'type': TaskGroup.TASK_GROUP_LIST_ID, 'index': self.id},
                style={"minHeight": "30px", "padding": "10px", "lineHeight": "36px"}
            )
        ])

        return detail_comp

    def show_ratio_bar(self):
        return True

    def get_successes(self):
        return sum(1 for t in self.tasks if t.task_status == TodoStatusEnum.DONE)

    def get_warnings(self):
        return 0

    def get_failures(self):
        return sum(1 for t in self.tasks if t.task_status == TodoStatusEnum.MISSED)

    def get_in_progress(self):
        return sum(1 for t in self.tasks if t.task_status == TodoStatusEnum.IN_PROGRESS)

    def get_num_pending(self):
        return sum(1 for t in self.tasks if t.task_status == TodoStatusEnum.TODO)

    @staticmethod
    def handle_add_task_to_task_group(n_clicks, task_name, btn_id, date_string, repeat_cycle):
        if n_clicks == 0:
            raise PreventUpdate()

        if btn_id['index'] in TaskGroup.instance_map:
            instance = TaskGroup.instance_map[btn_id['index']]
            return [
                instance.handle_add_task(
                    task_name, datetime.datetime.fromisoformat(date_string),
                    repeat_period=TaskRepeatPeriodEnum[repeat_cycle]
                ),
                details.render_summary_inner_div_from_detailable(instance)
            ]

        raise PreventUpdate()

    @staticmethod
    def handle_task_done_in_task_group(n_clicks, task_id):
        print(task_id)

    @staticmethod
    def get_callback_definitions():
        return [
            {
                "output": [
                    Output({'type': TaskGroup.TASK_GROUP_LIST_ID, 'index': MATCH}, 'children'),
                    Output({'type': TaskGroup.TASK_GROUP_SUMMARY_DIV_ID, 'index': MATCH}, 'children'),
                ],
                "inputs": [
                    Input({'type': TaskGroup.ADD_TASK_BTN_ID, 'index': MATCH}, 'n_clicks')
                ],
                "state": [
                    State({'type': TaskGroup.NEW_TASK_INPUT_ID, 'index': MATCH}, 'value'),
                    State({'type': TaskGroup.ADD_TASK_BTN_ID, 'index': MATCH}, 'id'),
                    State({'type': TaskGroup.TASK_GROUP_DUE_DATE_PICKER_ID, 'index': MATCH}, 'date'),
                    State({'type': TaskGroup.NEW_TASK_REPEATS_DROPDOWN_ID, 'index': MATCH}, 'value')
                ],
                "function": TaskGroup.handle_add_task_to_task_group
            },
            {
                "output": [
                    Output({'type': TaskGroup.TASK_GROUP_WRAPPER_DIV_ID, 'index': MATCH}, 'children')
                ],
                "inputs": [
                    Input({'type': Task.TASK_STATUS_BUTTON_1_ID, 'index': MATCH}, 'n_clicks')
                ],
                "state": [
                    State({'type': Task.TASK_STATUS_BUTTON_1_ID, 'index': MATCH}, 'id')
                ],
                "function": TaskGroup.handle_task_done_in_task_group
            }
        ]
