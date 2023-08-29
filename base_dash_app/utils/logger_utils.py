import logging
import sys
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


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level_color = LEVEL_COLORS.get(record.levelname, f"{BColors.WHITE}")
        level_endc = LEVEL_ENDC.get(record.levelname, f"{BColors.ENDC}")
        formatted_msg = super(ColoredFormatter, self).format(record)
        formatted_level = f'{level_color}{record.levelname}{level_endc}'
        return formatted_msg.replace(record.levelname, formatted_level)


LOGGING_FORMAT = f'{BColors.WHITE}[%(asctime)s]{BColors.ENDC}' \
                 f'{BColors.OKCYAN}[%(name)30s]{BColors.ENDC}' \
                 f'[%(levelname)10s]:' \
                 f'%(message)s'


def configure_logging(logging_format=None, log_level=None, stream=sys.stdout):
    if logging_format is None:
        logging_format = LOGGING_FORMAT

    if log_level is None:
        log_level = logging.INFO

    formatter = ColoredFormatter(logging_format)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


# configure_logging()
# logging.debug("Debug message")
# logging.info("Informational message")
# logging.warning("Warning message")
# logging.error("Error message")
# logging.critical("Critical message")
