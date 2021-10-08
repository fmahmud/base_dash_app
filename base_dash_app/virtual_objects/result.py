from base_dash_app.enums.status_colors import StatusColors


class Result:
    def __init__(self, result, status_color: StatusColors):
        self.result = result
        self.status_color: StatusColors = status_color
