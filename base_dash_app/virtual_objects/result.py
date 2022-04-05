from base_dash_app.enums.status_colors import StatusesEnum


class Result:
    def __init__(self, result, status: StatusesEnum):
        self.result = result
        self.status: StatusesEnum = status
