import logging

from base_dash_app.utils.bcolors import LEVEL_COLORS, BColors, LEVEL_ENDC


class ColoredFormatter(logging.Formatter):

    def __init__(self, log_format=None):
        self.log_format = log_format or (
            f'{BColors.WHITE}[%(asctime)s]{BColors.ENDC}'
            f'{BColors.OKCYAN}[%(name)30s]{BColors.ENDC}'
            f'[%(levelname)10s]: '
            f'%(message)s'
        )
        super().__init__(fmt=self.log_format)

    def format(self, record):
        level_color = LEVEL_COLORS.get(record.levelname, f"{BColors.WHITE}")
        level_endc = LEVEL_ENDC.get(record.levelname, f"{BColors.ENDC}")
        formatted_level = f'{level_color}{record.levelname:>10}{level_endc}'
        record.asctime = self.formatTime(record, self.datefmt)
        return (
            f"{BColors.WHITE}[{record.asctime}]{BColors.ENDC}"
            f"{BColors.OKCYAN}[{record.name:>30}]{BColors.ENDC}"
            f'[{formatted_level}]: '
            f'{record.getMessage()}'
        )

