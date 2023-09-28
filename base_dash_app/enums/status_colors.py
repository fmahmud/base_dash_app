from enum import unique, Enum


class Status:
    def __init__(self, id: int, name: str, hex_color: str, bootstrap_alt: str):
        self.id: int = id
        self.name: str = name
        self.hex_color: str = hex_color
        self.bootstrap_alt: str = bootstrap_alt


@unique
class StatusesEnum(Enum):
    SUCCESS = Status(1, "Success", "#2cbe4e", "success")
    WARNING = Status(2, "Warning", "#ffc107", "warning")
    FAILURE = Status(3, "Failure", "#dc3545", "danger")
    IN_PROGRESS = Status(4, "In Progress", "#009fff", "info")
    PENDING = Status(5, "Pending", "##91d6ff", "lightblue")
    NOT_STARTED = Status(6, "Not Started", "#aaaaaa", "grey")

    def __str__(self):
        return self.value.name

    @staticmethod
    def get_by_name(name: str):
        for e in StatusesEnum:
            if e.value.name.lower() == name.lower():
                return e

        raise Exception(f"Could not find StatusesEnum with name {name}")

    @staticmethod
    def get_by_id(id: int) -> 'StatusesEnum':
        for e in StatusesEnum:
            if e.value.id == id:
                return e

        raise Exception(f"Could not find StatusesEnum with id {id}.")

    @staticmethod
    def get_passing_statuses():
        return [StatusesEnum.SUCCESS, StatusesEnum.WARNING]

    @staticmethod
    def get_failing_statuses():
        return [StatusesEnum.FAILURE]

    @staticmethod
    def get_terminal_statuses():
        return [StatusesEnum.SUCCESS, StatusesEnum.WARNING, StatusesEnum.FAILURE, StatusesEnum.NOT_STARTED]

    @staticmethod
    def get_non_terminal_statuses():
        return [StatusesEnum.IN_PROGRESS, StatusesEnum.PENDING]


