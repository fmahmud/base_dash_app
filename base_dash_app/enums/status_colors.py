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
    PENDING = Status(5, "Pending", "#aaaaaa", "secondary")

    def __str__(self):
        return self.value.name

    @staticmethod
    def get_by_id(id: int) -> 'StatusesEnum':
        for e in StatusesEnum:
            if e.value.id == id:
                return e

        raise Exception(f"Could not find StatusesEnum with id {id}.")

