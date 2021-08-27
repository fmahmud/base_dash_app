from abc import ABC, abstractmethod
from typing import Callable, Optional

from base_dash_app.enums.status_colors import StatusColors


class Resultable(ABC):
    @abstractmethod
    def get_result(self, *, perspective: Callable[['Resultable'], Optional[int]] = None):
        """
        A resultable object contains a prior result, computed in the past. This function
        returns that value. Optionally, this result can have perspectives, in the case
        of a competition. The perspective function allows the implementer to supply the
        result from a perspective.
        :param perspective: function that assesses the Resultable that returns True if
          it is a victory for this perspective or False if it is a loss. Returns None
          if the perspective doesn't apply.
        :return:
        """
        pass

    @staticmethod
    def get_status_color_from_result(result):
        # todo: potentially bad as None means in progress and not included... fix
        if result is None:
            return StatusColors.IN_PROGRESS

        if result < 0:
            return StatusColors.FAILURE
        elif result == 0:
            return StatusColors.WARNING
        else:
            return StatusColors.SUCCESS

    @abstractmethod
    def get_status_color(self, *, perspective=None):
        return Resultable.get_status_color_from_result(self.get_result(perspective=perspective))