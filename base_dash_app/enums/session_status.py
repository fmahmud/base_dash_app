

from enum import Enum, unique

from base_dash_app.enums.status_colors import StatusesEnum


class SessionStatus:
    # should this return dictionaries instead?
    def __init__(self, id: int, name: str, status_color: StatusesEnum):
        self.id = id
        self.name = name
        self.color = status_color


@unique
class SessionStatuses(Enum):
    PENDING = SessionStatus(1, "Pending", StatusesEnum.PENDING)
    IN_PROGRESS = SessionStatus(2, "In Progress", StatusesEnum.IN_PROGRESS)
    COMPLETE_PERFECT = SessionStatus(3, "Successful", StatusesEnum.SUCCESS)
    COMPLETE_IMPERFECT = SessionStatus(4, "Test Errors", StatusesEnum.WARNING)
    FAILED = SessionStatus(5, "Execution Failed", StatusesEnum.FAILURE)

    def get_id(self):
        return self.value.id

    @staticmethod
    def get_by_id(id: int):
        for e in SessionStatuses:
            if e.value.id == id:
                return e
        raise Exception("SessionStatus with id %i does not exist." % id)
