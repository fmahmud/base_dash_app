import datetime
from typing import List, Callable, Optional

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.components.details.details import DetailTextItem
from base_dash_app.components.historicals import historical_dots

from base_dash_app.enums.task_repeat_period_enum import TaskRepeatPeriodEnum
from base_dash_app.enums.todo_status_enum import TodoStatusEnum
from base_dash_app.utils import utils
from base_dash_app.utils.utils import SIMPLE_DATE_FORMAT
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent
from base_dash_app.virtual_objects.interfaces.resultable import Resultable


class TaskInstance(ResultableEvent):

    # todo: remove this
    NUM_TASK_INSTANCES = 0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.id == other.id

    def get_result(self, *, perspective: Callable[[Resultable], Optional[int]] = None):
        return self.status.value

    def get_name(self):
        return self.task_template.task_name

    def get_header(self) -> (str, dict):
        pass

    def get_text(self) -> (str, dict):
        pass

    def get_extras(self):
        pass

    def get_link(self) -> str:
        pass

    def get_status_color(self, *, perspective=None):
        return self.status.color

    def __init__(self, task_template: 'Task', due_date: datetime.datetime):
        super().__init__(due_date)
        TaskInstance.NUM_TASK_INSTANCES += 1
        self.id: int = TaskInstance.NUM_TASK_INSTANCES
        self.task_template = task_template
        self.status: TodoStatusEnum = TodoStatusEnum.TODO


class Task:

    TASK_STATUS_BUTTON_1_ID = 'task-status-button-1-id'
    TASK_STATUS_BUTTON_2_ID = 'task-status-button-2-id'
    TASK_STATUS_BUTTON_3_ID = 'task-status-button-3-id'
    NUM_TASKS = 0

    def __init__(self, task_name: str, task_description: str = None,
                 task_group: 'TaskGroup' = None, first_due_date: datetime.datetime = None, priority: int = 0,
                 repeat_period: TaskRepeatPeriodEnum = TaskRepeatPeriodEnum.DOES_NOT_REPEAT):

        # temporary indexing
        from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
        Task.NUM_TASKS += 1

        self.id = Task.NUM_TASKS
        self.task_name: str = task_name
        self.task_description: str = task_description
        self.task_group: TaskGroup = task_group
        self.first_due_date: datetime.datetime = first_due_date
        self.priority: int = priority
        self.task_status: TodoStatusEnum = TodoStatusEnum.TODO
        self.repeat_period: TaskRepeatPeriodEnum = repeat_period
        self.tags: List[str] = []
        self.past_instances: List[TaskInstance] = []
        self.upcoming_instances: List[TaskInstance] = []

    def populate_next_due_date(self):
        next_due_date = None
        if len(self.upcoming_instances) == 0:
            previous_due_date = self.get_most_recent_due_date()
            if previous_due_date is None:
                next_due_date = self.first_due_date
        else:
            previous_due_date = self.upcoming_instances[-1].date

        if next_due_date is None:
            next_due_date = TaskRepeatPeriodEnum.get_next_occurrence(self.repeat_period, previous_due_date)

        self.upcoming_instances.append(TaskInstance(self, next_due_date))

    def get_most_recent_due_date(self) -> Optional[datetime.datetime]:
        if len(self.past_instances) > 0:
            return self.past_instances[-1].date
        return None

    def add_tag(self, tag):
        self.tags.append(tag)

    def get_height_override(self):
        return 20

    def get_summary_components(self) -> List[DetailTextItem]:
        task_text_item_style = {
            "height": "32px", "lineHeight": "32px", "fontSize": "14px"
        }

        to_return: List[DetailTextItem] = [
            DetailTextItem(
                historical_dots.render([self.task_status.color]),
                style={"width": "50px", "height": "100%"}
            ),
            DetailTextItem(self.task_name, utils.apply({"minWidth": "300px"}, task_text_item_style)),
            DetailTextItem(html.Div([
                html.H4(dbc.Badge(t, color="info"))
                for t in self.tags
            ]), utils.apply({"minWidth": "300px"}, task_text_item_style)),
            DetailTextItem(
                "Due by: %s" % datetime.datetime.strftime(self.first_due_date, SIMPLE_DATE_FORMAT),
                utils.apply({"minWidth": "300px"}, task_text_item_style)
            ),
            DetailTextItem(
                "Repeats: %s, next occurance: %s" % (
                    self.repeat_period.value,
                    datetime.datetime.strftime(
                        TaskRepeatPeriodEnum.get_next_occurrence(self.repeat_period, self.first_due_date),
                        utils.SIMPLE_DATE_FORMAT
                    )
                ),
                utils.apply({"minWidth": "300px"}, task_text_item_style)
            ) if self.repeat_period != TaskRepeatPeriodEnum.DOES_NOT_REPEAT else "",
            DetailTextItem(
                historical_dots.render([i.get_status_color() for i in self.past_instances]),
                {"minWidth": "300px"}
            ),
            DetailTextItem(
                dbc.ButtonGroup([
                    dbc.Button(
                        html.I(
                            className="fas fa-play"
                            if self.task_status == TodoStatusEnum.IN_PROGRESS else "fas fa-check"
                        ),
                        id={'type': Task.TASK_STATUS_BUTTON_1_ID, 'index': self.task_group.id, 'self_id': self.id},
                        n_clicks=0, size="sm", outline=True,
                        className="display_on_parent_hover_only",
                    ),
                    dbc.Button(
                        html.I(className="fas fa-pause"),
                        id={'type': Task.TASK_STATUS_BUTTON_2_ID, 'index': self.task_group.id, 'self_id': self.id},
                        n_clicks=0, size="sm", outline=True,
                        className="display_on_parent_hover_only",
                    ),
                    dbc.Button(
                        html.I(className="fas fa-check"),
                        id={'type': Task.TASK_STATUS_BUTTON_3_ID, 'index': self.task_group.id, 'self_id': self.id},
                        n_clicks=0, size="sm", outline=True,
                        className="display_on_parent_hover_only",
                    ),

                ]),
                utils.apply({"minWidth": "100px", "maxWidth": "100px", "float": "right"}, task_text_item_style)
            ),
        ]

        return to_return
