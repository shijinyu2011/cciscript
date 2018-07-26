import ConfigParser
import io
import os
import re
import getpass

from qcutils.log import Log
from qcutils.exception import QcUtilsException


class CannotOpenQcRcFile(QcUtilsException):
    pass


class QcConfig(object):

    def __init__(self):
#         self.config_path = os.path.join(os.path.expanduser("~"), '.qcutilsrc')
        self.config_path = os.path.normpath(os.path.join(__file__, '../../qcutilsrc.local'))
        self.config = {}
        self._read_config()

    def __getattr__(self, attr):
        return self.config.get(attr)

    @property
    def test_case_search_root(self):
        Log.info('Password not given in configuration %s' % self.config_path)
        tc_root = self.config.get('test_case_search_root')
        return re.sub('&', '&amp;', tc_root)

    @property
    def password(self):
        attr = 'password'
        if not self.config.get(attr):
            pw = getpass.getpass('Please enter password: ')
            self.config[attr] = pw
        return self.config.get(attr)

    @property
    def proxy(self):
        proxy = self.config.get('proxy')
        return {'http': proxy, 'https': proxy} if proxy else dict()

    def _read_config(self):
        '''
        Reads $HOME/.qcutilsrc that must contain:
        usenrname = username # NSN-Intra
        password = password # NSN-Intra, empty for QC QA server
        domain = SANDBOX
        project = Playground1
        server_url = http://87.254.209.238
        proxy =
        test_case_search_root = \\Subject\\
        '''
        try:
            virtual_file = io.StringIO(u'[dummy]\n%s' % open(self.config_path).read())
            config = ConfigParser.ConfigParser()
            config.readfp(virtual_file)
        except Exception, e:
            raise CannotOpenQcRcFile(e)
        for param in ['username', 'password', 'domain', 'project', 'xml_api_url',
                      'server_url', 'test_case_search_root', 'proxy']:
            self.config[param] = config.get('dummy', param)
