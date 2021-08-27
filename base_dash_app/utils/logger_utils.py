import logging

LOGGING_FORMAT = '[%(asctime)s][%(name)s]: %(message)s'


def configure_logging():
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.DEBUG)
