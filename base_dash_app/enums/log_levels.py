from enum import Enum

from base_dash_app.virtual_objects.interfaces.selectable import Selectable


class LogLevel(Selectable):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def get_label(self):
        return self.name

    def get_value(self):
        return self.id

    def __le__(self, other):
        if type(other) == type(self):
            return self.id <= other.id
        elif type(other) == LogLevelsEnum:
            return self.id <= other.value.id

        return False

    def __lt__(self, other):
        if type(other) == type(self):
            return self.id < other.id
        elif type(other) == LogLevelsEnum:
            return self.id < other.value.id

        return False


class LogLevelsEnum(Enum):
    TRACE = LogLevel(0, "trace")
    DEBUG = LogLevel(1, "debug")
    INFO = LogLevel(2, "info")
    WARNING = LogLevel(3, "warning")
    ERROR = LogLevel(4, "error")
    CRITICAL = LogLevel(5, "critical")

    @staticmethod
    def get_by_id(id) -> LogLevel:
        for e in LogLevelsEnum:
            if e.value.id == id:
                return e.value

        raise Exception(f"No such enum with id {id} was found.")
