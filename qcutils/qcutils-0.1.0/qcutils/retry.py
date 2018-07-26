import time

from qcutils.log import Log


class RetryLimitExceeded(Exception):
    pass


class RetryDelay(object):

    def __init__(self, max_retry_attempts=0):
        self.max_attempts = max_retry_attempts
        self.sleep_sequence = [2, 2, 5, 10, 15, 20, 30, 60]
        self.attempt = 0

    def next_sleep(self):
        if self.attempt < len(self.sleep_sequence):
            return self.sleep_sequence[self.attempt]
        else:
            return self.sleep_sequence[-1]

    def wait(self):
        if self.attempt >= self.max_attempts:
            raise RetryLimitExceeded(self.max_attempts)
        Log.debug("Retry attempt:%s, next sleep:%s" % (self.attempt, self.next_sleep()))
        time.sleep(self.next_sleep())
        self.attempt += 1
