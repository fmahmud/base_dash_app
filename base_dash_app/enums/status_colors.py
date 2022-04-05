from enum import unique, Enum


class Status:
    def __init__(self, name: str, hex_color: str, bootstrap_alt: str):
        self.name: str = name
        self.hex_color: str = hex_color
        self.bootstrap_alt: str = bootstrap_alt


@unique
class StatusesEnum(Enum):
    SUCCESS = Status("Success", "#2cbe4e", "success")
    WARNING = Status("Warning", "#ffc107", "warning")
    FAILURE = Status("Failure", "#dc3545", "danger")
    IN_PROGRESS = Status("In Progress", "#009fff", "info")
    PENDING = Status("Pending", "#aaaaaa", "secondary")

    def __str__(self):
        return self.value.hex_color

