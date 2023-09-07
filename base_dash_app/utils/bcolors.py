from enum import Enum


class BColors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[37m'
    ENDC = '\033[0m'

    def __str__(self):
        return self.value


LEVEL_COLORS = {
    'DEBUG': f"{BColors.OKBLUE}",
    'INFO': f"{BColors.OKGREEN}",
    'WARNING': f"{BColors.WARNING}",
    'ERROR': f"{BColors.FAIL}",
    'CRITICAL': f"{BColors.BOLD}{BColors.FAIL}"
}
LEVEL_ENDC = {
    'DEBUG': f"{BColors.ENDC}",
    'INFO': f"{BColors.ENDC}",
    'WARNING': f"{BColors.ENDC}",
    'ERROR': f"{BColors.ENDC}",
    'CRITICAL': f"{BColors.ENDC}{BColors.ENDC}"
}
