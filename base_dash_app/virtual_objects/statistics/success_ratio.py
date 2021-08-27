from base_dash_app.virtual_objects.statistics.statistic import Statistic


class SuccessRatio(Statistic):
    def __init__(self):
        super().__init__()
        self.count = 0

    def process_result(self, result: float):
        result = result * 0.5 + 0.5
        self.value = ((self.value * self.count) + result) / (self.count + 1)
        self.count += 1