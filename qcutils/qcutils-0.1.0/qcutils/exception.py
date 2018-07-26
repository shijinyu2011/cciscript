

class QcUtilsException(Exception):
    pass


class QcUtilsDetailedException(QcUtilsException):
    def __init__(self, msg, detail):
        super(QcUtilsDetailedException, self).__init__(msg)
        self.detail = detail
