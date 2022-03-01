from enum import unique, Enum


class StatusColor:
    def __init__(self, hex_color: str, bootstrap_alt: str):
        self.hex_color: str = hex_color
        self.bootstrap_alt: str = bootstrap_alt


@unique
class StatusColors(Enum):
    SUCCESS = StatusColor("#2cbe4e", "success")
    WARNING = StatusColor("#ffc107", "warning")
    FAILURE = StatusColor("#dc3545", "danger")
    IN_PROGRESS = StatusColor("#009fff", "info")
    PENDING = StatusColor("#aaaaaa", "secondary")

    def __str__(self):
        return self.value.hex_color

