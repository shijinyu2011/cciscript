import re
import copy

from qcutils.log import Log
from qcutils.client.qcclient import QcClientException
from qcutils.client.rest.query import RestQuery, RestHeaderQuery


class QcRestClient(object):

    def __init__(self, server, username, password, domain, project, proxy):
        super(QcRestClient, self).__init__()
        self.server = server
        self.username = username
        self.password = password
        self.domain = domain
        self.project = project
        self.proxy = proxy
        self.cookie = None
        logvars = copy.deepcopy(vars())
        del logvars['password']
        Log.debug('Initialized QC REST client with: %s' % logvars)

    @property
    def base_path(self):
        return 'qcbin/rest/domains/%s/projects/%s/' % (self.domain, self.project)

    @staticmethod
    def equals_query(queries):
        """
        Query to be appended to URL after "?"
        queries - dict of key-value pairs that must match. e.g. {'user-01': 'EXAMPLE_001'}}
        No support for spaces or special characters. Add the support in this fuction if you need them.
        """
        key_value_pair_strings = []
        for key, value in queries.items():
            if type(value) is str:
                value = value.replace('&', '%26')
            if type(value) == int:
                value_str = '%s' % value
            else:
                value_str = "'%s'" % value
            Log.debug("############################# STR: %s" % value_str)
            key_value_pair_strings.append('%s[%s]' % (key, value_str))
        return "query={%s}" % (';'.join(key_value_pair_strings))

    def query(self, path_frag, query_type='get', data='', result=200):
        """
        :path_frag  A path to append to base path
        :data  JSON formatted data to send
        """
        path = self.base_path + path_frag
        q = RestQuery(path, query_type, data=data, result=result)
        response = q.request(self.server,
                             headers={'Cookie': self.cookie},
                             content_type='application/json',
                             proxies=self.proxy)
        return response

    @staticmethod
    def debug_print_fields(entity, title=None):
        if title:
            Log.debug(title)
        else:
            Log.debug("----------------------------------")
        for field in entity['Fields']:
            for value in field['values']:
                if 'value' in value:
                    Log.debug("%-20s: %s" % (field['Name'], value['value']))

    @staticmethod
    def get_field_value(entity, field_name):
        for field in entity['Fields']:
            for value in field['values']:
                if field['Name'] == field_name:
                    return value['value']

    def authenticate(self):
        path = 'qcbin/authentication-point/alm-authenticate'
        data = ("<?xml version='1.0' encoding='utf-8'?>"
                "<alm-authentication>"
                "<user>%s</user>"
                "<password>%s</password>"
                "</alm-authentication>") % (self.username, self.password)
        q = RestHeaderQuery(path, "post", data=data)
        headers = q.request(self.server, proxies=self.proxy)
        self.cookie = headers['set-cookie']
        Log.debug("Got cookie: %s" % self.cookie)

    def resolveTestFolderQcId(self, folder_path):
        folder_path_dirs = re.split(r'[/\\]', folder_path)
        parent_id = 0
        parent_name = ""
        for d in folder_path_dirs:
            path_frag = 'test-folders?' + self.equals_query({'parent-id': parent_id, 'name': d})
            response = self.query(path_frag)
            if int(response['TotalResults']) < 1:
                raise QcClientException('No matches found with dir "%s" and parent \"%s\"' % (d, parent_name))
            if int(response['TotalResults']) > 1:
                raise QcClientException('More than one match found with dir "%s" and parent \"%s\"' % (d, parent_name))
            entity = response['entities'][0]
            self.debug_print_fields(entity)
            Log.debug('dir \"%s\" found' % (d))
            parent_id = self.get_field_value(entity, 'id')
            parent_name = self.get_field_value(entity, 'name')
        return self.get_field_value(entity, 'id')

    @staticmethod
    def _buildTestCaseData(test_id, test_name, parent_id, priority):
        priority_map = {'must': '1-Must',
                        'should': '2-Should',
                        'could': '3-Could',
                        'wont': '4-Wont'}
        data = ('{"Fields":['
                '{"Name":"parent-id","values":[{"value":"%(parent_id)s"}]},'
                '{"Name":"user-01","values":[{"value":"%(test_id)s"}]},'
                '{"Name":"name","values":[{"value":"%(test_name)s"}]},'
                '{"Name":"subtype-id","values":[{"value":"MANUAL"}]},'
                '{"Name":"user-10","values":[{"value":"ET - Functional Test"}]},'
                '{"Name":"user-11","values":[{"value":"Feature"}]},'
                '{"Name":"user-12","values":[{"value":"Fully automated"}]},'
                '{"Name":"user-19","values":[{"value":"Dummy"}]},'
                '{"Name":"user-20","values":[{"value":"Dummy"}]},'
                '{"Name":"user-26","values":[{"value":"22 Execution fully - Analysis fully"}]},'
                '{"Name":"user-43","values":[{"value":"%(priority)s"}]}'
                ']}'
                % ({'parent_id': parent_id,
                    'test_id': test_id,
                    'test_name': test_id + '_' + test_name if test_name else test_id,
                    'priority': priority_map[priority]}))
        return data

    def updateTestCase(self, existing_test_id, parent_id, test_id, test_name, priority='should'):
        data = self._buildTestCaseData(test_id, test_name, parent_id, priority)
        response = self.query('tests/%s' % existing_test_id, 'put', data, 200)
        self.debug_print_fields(response, "Updated test case")

    def addTestCase(self, parent_id, test_id, test_name, priority='should'):
        data = self._buildTestCaseData(test_id, test_name, parent_id, priority)
        response = self.query('tests', 'post', data, 201)
        self.debug_print_fields(response, "Added test case")
        return self.get_field_value(response, 'id')

    def getReqCoverageByTCID(self, test_case_id):
        query_params = {'test-id': test_case_id}
        response = self.query('requirement-coverages?' + self.equals_query(query_params))
        req_coverage = {}
        for entity in response['entities']:
            self.debug_print_fields(entity)
            req_coverage.update({self.get_field_value(entity, 'requirement-id'):
                                 self.get_field_value(entity, 'id')})
        return req_coverage

    def addReqCoverage(self, qc_test_id, requirement_id):
        data = ('{"Fields":['
                '{"Name":"requirement-id","values":[{"value":"%s"}]},'
                '{"Name":"test-id","values":[{"value":"%s"}]}'
                ']}'
              % (requirement_id, qc_test_id))
        response = self.query('requirement-coverages', 'post', data, 201)
        self.debug_print_fields(response, "Added requirement coverage")

    def getTestCaseByTCID(self, test_case_id, parent_id=None, raise_on_empty_match=True):
        query_params = {'user-01': test_case_id}
        if parent_id:
            query_params.update({'parent-id': parent_id})
        response = self.query('tests?' + self.equals_query(query_params))
        test_ids = []
        for entity in response['entities']:
            self.debug_print_fields(entity)
            test_ids.append(self.get_field_value(entity, 'id'))
        if int(response['TotalResults']) < 1:
            if raise_on_empty_match:
                raise QcClientException('No test cases found with Test Case ID "%s"' % (test_case_id))
            else:
                return None
        if int(response['TotalResults']) > 1:
            raise QcClientException('More than one test case found with Test Case ID "%s" (IDs: %s) ' %
                                    (test_case_id, ''.join(test_ids)))
        return test_ids[0]


if __name__ == "__main__":
    pass
