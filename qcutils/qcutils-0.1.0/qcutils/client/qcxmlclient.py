from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor
import re
import time
from xml.etree import ElementTree

from qcutils.log import Log
from qcutils.retry import RetryDelay
from qcutils.client.qcclient import QcClientException, QcClientDetailedException


class QcXmlException(QcClientDetailedException):
    pass


class QcXmlClient(object):
    '''
    Python API for reporting Robot test results to QualityCenter.

    All API SOAP methods take single string argument where the string must
    contain XML input specific to the method. Documentation and examples of
    correctly formatted input XMLs can be found in
    https://confluence.inside.nsn.com/display/QC/QCXML+WebService

    NOTE: QC XML is very unreliable. Methods can return "502 Proxy Error" for
    no apparent reason. That's why we have RetryTimer
    '''

    def __init__(self, xml_api_url, username, password, domain, project, test_case_search_root, proxy=None):
        super(QcXmlClient, self).__init__()
        self.url = xml_api_url
        self.username = username
        self.password = password
        self.domain = domain
        self.project = project
        self.test_case_search_root = test_case_search_root
        self.proxy = proxy
        self.client = None

    def initialize(self):
        ns = 'http://nokiasiemensnetworks.com/QCXML'
        imp = Import(ns)
        doctor = ImportDoctor(imp)
        self.client = Client(self.url, location=self.url, proxy=self.proxy, doctor=doctor)
        self.client.set_options(service='QcXmlWebService', port='QcXmlWebServiceSoap12')

    def _constructInputXML(self, operation, parameters=None):
        input_xml = ElementTree.Element(operation)
        login = ElementTree.SubElement(input_xml, 'login')
        domain = ElementTree.SubElement(login, 'domain_name')
        project = ElementTree.SubElement(login, 'project_name')
        username = ElementTree.SubElement(login, 'user_name')
        password = ElementTree.SubElement(login, 'password')
        domain.text = self.domain
        project.text = self.project
        username.text = self.username
        password.text = self.password
        if parameters is not None:
            input_xml.append(parameters)
        return ElementTree.tostring(input_xml)

    @staticmethod
    def _FilterQcXmlExceptions(xml):
        response = ElementTree.XML(xml)
        if response.findall('error_message'):
            msg = response.findall('error_message')[0].text
            detail = None
            if response.findall('error_additional_info'):
                detail = response.findall('error_additional_info')[0].text
            raise QcXmlException(msg, detail)
        return xml

    @staticmethod
    def _removePassword(string):
        return re.sub(r'<password>(.*)</password>', '<password>********</password>', string)

    def _QcXmlApiCall(self, method_name, inputXML):
        Log.debug('Calling %s on %s' % (method_name, self.url))
        delay = RetryDelay(40)
        while True:
            try:
                ret = getattr(self.client.service, method_name)(inputXML)
                return self._FilterQcXmlExceptions(ret)
            except QcXmlException:
                raise
            except Exception, e:
                Log.warn('Temporary problem in QualityCenter (%s). Retrying in %s s...' %
                                    (e, delay.next_sleep()))
                delay.wait()  # Will throw exception after max attempts
                self.initialize()

    def GetVersion(self):
        ret = self.client.service.GetVersion()
        return ret

    def GetUserProjects(self):
        '''
        Excpected return value from API
        <return_message>
          <status>True</status>
          <return_value>
            <project_name>FP</project_name>
          </return_value>
        </return_message>
        '''
        input_xml = self._constructInputXML('GetUserProjects')
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("GetUserProjects", input_xml)
        element = ElementTree.XML(returnXML)
        return [x.text for x in element.findall('return_value')[0].findall('project_name')]

    def FindTestCase(self, test_case_id, path=None):
        '''
        Finds test case's numeric ID by the test_case_id string.
        test_case_id is the "Test Case ID" in QC web UI. In the database
        this field is called TS_USER_01. Numeric test case id is internal
        to QC and not visible in the web user interface.

        Expected return value, e.g.
            <return_message>
              <status>True</status>
              <return_value>
                <test_case>
                  <id>28</id>
                  <name>Authentication configuration of NTP</name>
                  <path>\Subject\VGP&amp;LCC\NECC\Operability Interfaces\NTP\NECC provides clock synchronization to vNE</path>
                </test_case>
              </return_value>
            </return_message>
        '''
        if not path:
            path = self.test_case_search_root
        parameters = ElementTree.Element('parameters')
        path_elem = ElementTree.SubElement(parameters, 'path')
        ElementTree.SubElement(parameters, 'recursive').text = 'true'
        ElementTree.SubElement(parameters, 'include_attachments').text = 'false'
        ElementTree.SubElement(parameters, 'include_test_case_details').text = 'false'
        fields = ElementTree.SubElement(parameters, 'fields')
        test_case_id_elem = ElementTree.SubElement(fields, 'TS_USER_01')
        path_elem.text = path
        test_case_id_elem.text = '"%s"' % test_case_id
        input_xml = self._constructInputXML('GetTestCaseList', parameters)
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("GetTestCaseList", input_xml)
        element = ElementTree.XML(returnXML)
        testcases = element.findall('return_value')[0].findall('test_case')
        if len(testcases) > 1:
            raise QcClientException("Test case ID %s is not unique. Candidates are: %s" %
                                    (test_case_id, [x.findall('name')[0].text for x in testcases]))
        elif len(testcases) < 1:
            raise QcClientException('No test cases found with ID "%s" under path "%s"' %
                                    (test_case_id, self.test_case_search_root))
        else:
            return testcases[0].findall('id')[0].text

    def FindTestSet(self, path, test_set_name):
        '''
        Finds test set id by the test set name
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'path').text = path
        ElementTree.SubElement(parameters, 'include_attachments').text = 'false'
        ElementTree.SubElement(parameters, 'include_test_set_details').text = 'false'
        ElementTree.SubElement(parameters, 'recursive').text = 'false'
        fields = ElementTree.SubElement(parameters, 'fields')
        ElementTree.SubElement(fields, 'CY_CYCLE').text = '"%s"' % test_set_name
        input_xml = self._constructInputXML('GetTestSetList', parameters)
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("GetTestSetList", input_xml)
        element = ElementTree.XML(returnXML)
        testsets = element.findall('return_value')[0].findall('test_set')
        if len(testsets) > 1:
            raise QcClientException("Test set %s is not unique. Candidates are: %s" %
                                    (test_set_name, [x.findall('name')[0].text for x in testsets]))
        elif len(testsets) < 1:
            raise QcClientException("No test sets found with name %s" % (test_set_name))
        else:
            return testsets[0].findall('id')[0].text

    def FindTestSetFolder(self, path, folder_name):
        '''
        Finds test set folder by the folder name
        More details, See: <https://qc-api.inside.nsn.com/QcXmlWebSite/>
        Excpected return value from API
        <return_message>
            <status>True</status>
            <return_value>
                <folder_tree_node>
                    <folder>
                        <name>lidong_test</name>
                        <path>Root\lidong_test</path>
                    </folder>
                  <folder_tree_node>
                      <folder>
                          <name>testfolder_cj_01</name>
                          <path>Root\lidong_test\testfolder_cj_01</path>
                      </folder>
                    </folder_tree_node>
                    <folder_tree_node>
                        <folder>
                            <name>testfolder_cj_02</name>
                            <path>Root\lidong_test\testfolder_cj_02</path>
                        </folder>
                    </folder_tree_node>
                </folder_tree_node>
            </return_value>
        </return_message>
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'path').text = path
        ElementTree.SubElement(parameters, 'include_attachments').text = 'false'        
        ElementTree.SubElement(parameters, 'recursive').text = 'false'
        input_xml = self._constructInputXML('GetTestSetFolderTree', parameters)
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("GetTestSetFolderTree", input_xml)
        element = ElementTree.XML(returnXML)
        nodes = element.findall('return_value')[0].findall('folder_tree_node')
#         parent = nodes[0].findall('folder')[0].findall('name')[0].text
        childrens = [n[0].findall('name')[0].text for n in nodes[0].findall('folder_tree_node')]
        return (folder_name in childrens)    

    def GetTestSetInstances(self, test_set_id):
        '''
        Get a list of test case IDs that have already been added in this test set.

        Return value from GetTestSet api call is very long. We need to check if the test
        instance corresponding the test case is already added, so the essentials are:
            <return_message>
              <status>True</status>
              <return_value>
                <test_set>
                  <id>1207</id>
                  <name>QC Integration Test Test Set</name>
                  <fields>
                    ...
                  </fields>
                  <test_instance>
                    <id>63</id>
                    <name>[7]Example TC</name>
                    <fields>
                      ...
                      <TC_TEST_ID label="Test" type="number" size="10">1</TC_TEST_ID>
                      ...
                    </fields>
                  </test_instance>
                  ...
                </test_set>
              </return_value>
            </return_message>
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'include_attachments').text = 'false'
        ElementTree.SubElement(parameters, 'include_test_cases').text = 'false'
        set_fields = ElementTree.SubElement(parameters, 'testset_fields')
        ElementTree.SubElement(set_fields, 'CY_CYCLE_ID').text = 'CY_CYCLE_ID'
        instance_fields = ElementTree.SubElement(parameters, 'testinstance_fields')
        ElementTree.SubElement(instance_fields, 'TC_TEST_ID').text = 'TC_TEST_ID'
        ElementTree.SubElement(parameters, 'id').text = test_set_id
        input_xml = self._constructInputXML('GetTestSetByID', parameters)
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("GetTestSetByID", input_xml)
        Log.debug(returnXML)
        element = ElementTree.XML(returnXML)
        test_instances = element.findall('return_value')[0].findall('test_set')[0].findall('test_instance')
        instances_for_cases = dict()
        for i in test_instances:
            instance_qcid = i.findall('id')[0].text
            test_qcid = i.findall('fields')[0].findall('TC_TEST_ID')[0].text
            Log.debug('Test Case "%s" has a Test Instance "%s" in this test set' % (test_qcid, instance_qcid))
            instances_for_cases[test_qcid] = instance_qcid
        return instances_for_cases

    def AddTestToTestSet(self, test_case_id, test_set_id):
        '''
        See https://sharenet-ims.inside.nsn.com/livelink/livelink/Download/392499262

        Return value is very intersting, because it tells the test instance ID:
            <return_message>
              <status>True</status>
              <return_value>
                <test_instance_id>62</test_instance_id>
              </return_value>
            </return_message>
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'test_set_id').text = test_set_id
        instances = ElementTree.SubElement(parameters, 'test_instances')
        instance = ElementTree.SubElement(instances, 'test_instance')
        fields = ElementTree.SubElement(instance, 'fields')
        ElementTree.SubElement(fields, 'TC_TEST_ID').text = test_case_id
        ElementTree.SubElement(instance, 'attachments')
        input_xml = self._constructInputXML('AddTests2TestSet', parameters)
        Log.debug(self._removePassword(input_xml))
        returnXML = self._QcXmlApiCall("AddTests2TestSet", input_xml)
        element = ElementTree.XML(returnXML)
        test_instance_ids = element.findall('return_value')[0].findall('test_instance_id')
        if len(test_instance_ids) != 1:
            raise Exception("Did not get unique (or any) test instance ID.")
        else:
            return test_instance_ids[0].text

    def AddRunToTestSet(self, test_case_id, test_set_id, result, release=None, build=None, set_date=True):
        '''
        See https://sharenet-ims.inside.nsn.com/livelink/livelink/Download/392499262
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'test_set_id').text = test_set_id
        runs = ElementTree.SubElement(parameters, 'runs')
        run = ElementTree.SubElement(runs, 'run')
        ElementTree.SubElement(run, 'attachments')
        fields = ElementTree.SubElement(run, 'fields')
        ElementTree.SubElement(fields, 'RN_RUN_NAME').text = 'CloudTAF %s' % time.ctime()
        if set_date:
            ElementTree.SubElement(fields, 'RN_EXECUTION_DATE').text = time.strftime("%Y-%m-%d", time.gmtime())
            ElementTree.SubElement(fields, 'RN_EXECUTION_TIME').text = time.strftime("%H:%M:%S", time.gmtime())
        if release:
            ElementTree.SubElement(fields, 'RN_USER_03').text = release
        if build:
            ElementTree.SubElement(fields, 'RN_USER_01').text = build
        ElementTree.SubElement(fields, 'RN_TESTCYCL_ID').text = test_case_id
        ElementTree.SubElement(fields, 'RN_STATUS').text = result
        run = ElementTree.SubElement(run, 'steps')
        input_xml = self._constructInputXML('AddTestSetRuns', parameters)
        Log.debug(self._removePassword(input_xml))
        self._QcXmlApiCall("AddTestSetRuns", input_xml)

    def AddTestSetFolder(self, path, folder_name):
        '''
        Add test set folder by path and folder name
        More details, See: <https://qc-api.inside.nsn.com/QcXmlWebSite/>
        Excpected return value from API
        <return_message>
          <status>True</status>
          <return_value>
            <id>62</id>
          </return_value>
        </return_message>
        '''
        parameters = ElementTree.Element('parameters')        
        test_set_folder = ElementTree.SubElement(parameters, 'folder')
        ElementTree.SubElement(test_set_folder, 'attachments').text = ''
        ElementTree.SubElement(test_set_folder, 'name').text = folder_name
        ElementTree.SubElement(test_set_folder, 'path').text = path        
        input_xml = self._constructInputXML('AddTestSetFolder', parameters)
        Log.debug(self._removePassword(input_xml))
        
        returnXML = self._QcXmlApiCall("AddTestSetFolder", input_xml)
        element = ElementTree.XML(returnXML)             
        return element.findall('return_value')[0].findall('id')[0].text        
        
    def AddTestSet(self, path, test_set_name):
        '''
        Add test set by path and name
        More details, See: <https://qc-api.inside.nsn.com/QcXmlWebSite/>
        Excpected return value from API
        <return_message>
          <status>True</status>
          <return_value>
            <id>1803</id>
          </return_value>
        </return_message>
        '''
        parameters = ElementTree.Element('parameters')
        ElementTree.SubElement(parameters, 'path').text = path
        test_set = ElementTree.SubElement(parameters, 'test_set')
        ElementTree.SubElement(test_set, 'attachments').text = ''
        fields = ElementTree.SubElement(test_set, 'fields')
        ElementTree.SubElement(fields, 'CY_CYCLE').text = test_set_name
        ElementTree.SubElement(fields, 'CY_USER_01').text = 'RCP0'
        ElementTree.SubElement(fields, 'CY_USER_02').text = 'EnTe - Functional Test'
        ElementTree.SubElement(fields, 'CY_USER_13').text = 'Draft'
        ElementTree.SubElement(fields, 'CY_USER_18').text = 'N/A'
        ElementTree.SubElement(fields, 'CY_USER_51').text = 'cWLC'
        input_xml = self._constructInputXML('AddTestSet', parameters)
        Log.debug(self._removePassword(input_xml))

        returnXML = self._QcXmlApiCall("AddTestSet", input_xml)
        element = ElementTree.XML(returnXML)        
        return element.findall('return_value')[0].findall('id')[0].text
