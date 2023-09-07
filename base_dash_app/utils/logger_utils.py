import logging
import sys

from base_dash_app.utils.bcolors import BColors

LOGGING_FORMAT = f'{BColors.WHITE}[%(asctime)s]{BColors.ENDC}' \
                 f'{BColors.OKCYAN}[%(name)30s]{BColors.ENDC}' \
                 f'{BColors.BOLD}[%(levelname)10s]:{BColors.ENDC} ' \
                 f'%(message)s'


def configure_logging(
        logging_format=None,
        log_level=None,
        std_out_formatter=None,
        std_err_formatter=None
):
    if logging_format is None:
        logging_format = LOGGING_FORMAT

    if log_level is None:
        log_level = logging.INFO

    if std_out_formatter is not None:
        std_out_handler = logging.StreamHandler(sys.stdout)
        std_out_handler.setFormatter(std_out_formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(std_out_handler)
        root_logger.setLevel(log_level)
    else:
        logging.basicConfig(format=logging_format, level=log_level, stream=sys.stdout)

    if std_err_formatter is not None:
        std_err_handler = logging.StreamHandler(sys.stderr)
        std_err_handler.setFormatter(std_err_formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(std_err_handler)
        root_logger.setLevel(log_level)




# configure_logging()
# logging.debug("Debug message")
# logging.info("Informational message")
# logging.warning("Warning message")
# logging.error("Error message")
# logging.critical("Critical message")
