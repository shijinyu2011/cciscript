
from qcutils.log import Log
from qcutils.qcconfig import QcConfig
from qcutils.exception import QcUtilsException
from qcutils.client.qcrestclient import QcRestClient
from qcutils.client.qcxmlclient import QcXmlClient


class QcHandlerException(QcUtilsException):
    pass


class QcHandler(object):
    '''
    This handles the communication with the Quality Center, the derivative classes
    shall have different client serving different connection methods such
    as XML SOAP and REST.
    '''

    def __init__(self):
        self.parser = None
        self.config = QcConfig()
        self.client = None

    def initialize_client(self):
        '''
        Should initialize the self.client
        '''
        raise QcHandlerException('Please override, must initialize the self.client')

    def run(self, args):
        raise QcHandlerException('Please override, implement the script logic here')


class QcRestHandler(QcHandler):
    '''
    This is the handler for QC utilizing REST API
    '''
    def initialize_client(self):
        self.client = QcRestClient(self.config.server_url,
                                   self.config.username,
                                   self.config.password,
                                   self.config.domain,
                                   self.config.project,
                                   self.config.proxy)
        Log.critical("Authenticating to QC REST API...")
        self.client.authenticate()


class QcXmlHandler(QcHandler):
    '''
    This is the handler for QC utilizing XML API
    '''
    def initialize_client(self):
        self.client = QcXmlClient(self.config.xml_api_url,
                                  self.config.username,
                                  self.config.password,
                                  self.config.domain,
                                  self.config.project,
                                  self.config.test_case_search_root,
                                  self.config.proxy)
        Log.critical("Initialized QC XML API client")
        self.client.initialize()


if __name__ == "__main__":
    pass
