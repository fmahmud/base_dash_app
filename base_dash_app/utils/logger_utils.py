import logging
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


LOGGING_FORMAT = f'{BColors.WHITE}[%(asctime)s]{BColors.ENDC}{BColors.OKCYAN}[%(name)20s]{BColors.ENDC}: %(message)s'


def configure_logging(logging_format=None, log_level=None):
    if logging_format is None:
        logging_format = LOGGING_FORMAT

    if log_level is None:
        log_level = logging.INFO

    logging.basicConfig(format=logging_format, level=log_level)
