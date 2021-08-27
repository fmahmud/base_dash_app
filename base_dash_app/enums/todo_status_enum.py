from enum import Enum

from base_dash_app.enums.status_colors import StatusColors


class TodoStatusEnum(Enum):
    DONE = ("Done", StatusColors.SUCCESS)
    TODO = ("To do", StatusColors.PENDING)
    IN_PROGRESS = ("In Progress", StatusColors.IN_PROGRESS)
    MISSED = ("Missed", StatusColors.FAILURE)
    BLOCKED = ("Blocked", StatusColors.WARNING)

    def get_name(self):
        return self.status_name

    def get_color(self):
        return self.color.value

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, status_name: str, color: StatusColors):
        self.status_name = status_name
        self.color = color
