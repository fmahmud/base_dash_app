from enum import unique, Enum


@unique
class StatusColors(Enum):
    SUCCESS = "#2cbe4e"
    WARNING = "#ffc107"
    FAILURE = "#dc3545"
    IN_PROGRESS = "#009fff"
    PENDING = "#aaaaaa"

    def __str__(self):
        return self.value