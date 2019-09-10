import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_logger():
    return logger


def get_file_logger(path, custom_format=DEFAULT_FORMAT):
    f_handler = logging.FileHandler(path)
    f_format = logging.Formatter(custom_format)
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
