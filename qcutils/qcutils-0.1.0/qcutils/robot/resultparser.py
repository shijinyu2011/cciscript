import re
from xml.etree import ElementTree

from qcutils.log import Log


class RobotResultParser(object):

    def __init__(self, resultfile):
        self.file = resultfile

    def get_results(self):
        results = []
        element = ElementTree.parse(self.file).getroot()
        for i in element.getiterator():
            if i.tag == 'test':
                statuses = i.findall('status')
                assert(len(statuses) == 1)
                name = i.get('name')
                test_case_doc = i.findall('doc')[0].text
                test_case_id = name  # Fallback, if ID is not specified in the documentation
                if test_case_doc:
                    match = re.search(r'\bTEST_CASE_ID=(\w+)\b', test_case_doc)
                    if match:
                        test_case_id = match.group(1)
                status = statuses[0].get('status')
                results.append({'test_case_id': test_case_id, 'name': name, 'status': status})
        self.print_results(results)
        return results

    @staticmethod
    def print_results(results):
        Log.debug("Found the following test results to report")
        for r in results:
            Log.debug('%s (%s): %s' % (r['name'], r['test_case_id'], r['status']))
