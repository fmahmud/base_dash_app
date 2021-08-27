from base_dash_app.virtual_objects.statistics.statistic import Statistic


class BestStreak(Statistic):
    def __init__(self):
        super().__init__()
        self.current_streak = 0
        self.streaks = []

    def process_result(self, result: float):
        if result > 0:
            # win
            self.current_streak += 1

        else:
            # draw or loss
            if self.current_streak > 0:
                self.streaks.append(self.current_streak)
            self.current_streak = 0

    def get_statistic(self):
        return max(self.streaks + [self.current_streak])


class WorstStreak(Statistic):
    def __init__(self):
        super().__init__()
        self.worst_streak = 0
        self.current_streak = 0
        self.streaks = []

    def process_result(self, result: float):
        if result < 0:
            # loss
            self.current_streak += 1
        else:
            # draw or loss
            if self.current_streak > 0:
                self.streaks.append(self.current_streak)
            self.current_streak = 0

    def get_statistic(self):
        return max(self.streaks + [self.current_streak])