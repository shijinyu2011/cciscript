import logging
import logging.config
import os.path


def get_logger(logger_name):
    path = os.path.dirname(__file__)
    logging.config.fileConfig(os.path.join(path, 'logging.conf'))
    root_logger = logging.getLogger('main')
    return root_logger
