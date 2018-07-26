
import logging


class Log(object):

    logger = logging.getLogger(__name__)

    @classmethod
    def get_logger(cls):
        return cls.logger

    @classmethod
    def set_logging(cls, verbosity):
        '''
        Log levels are: 0, 1, 2, >2
        '''
        if verbosity > 1:
            logging.basicConfig(level=logging.CRITICAL, format="%(asctime)-15s %(message)s")
        else:
            logging.basicConfig(level=logging.CRITICAL, format="%(message)s")
        if verbosity <= 1:
            cls.logger.setLevel(logging.INFO)
        elif verbosity == 2:
            cls.logger.setLevel(logging.DEBUG)
        elif verbosity > 2:
            cls.logger.setLevel(1)

    @classmethod
    def log(cls, prio, msg):
        cls.logger.log(prio, msg)

    @classmethod
    def debug(cls, msg):
        cls.logger.debug(msg)

    @classmethod
    def info(cls, msg):
        cls.logger.info(msg)

    @classmethod
    def warn(cls, msg):
        cls.logger.warn(msg)

    @classmethod
    def error(cls, msg):
        cls.logger.error(msg)

    @classmethod
    def critical(cls, msg):
        cls.logger.critical(msg)
