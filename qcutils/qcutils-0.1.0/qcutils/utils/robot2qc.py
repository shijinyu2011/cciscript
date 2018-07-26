import argparse
import re

from qcutils.log import Log
from qcutils.qchandler import QcXmlHandler, QcHandlerException
from qcutils.robot.resultparser import RobotResultParser


class QcReporterException(QcHandlerException):
    pass


class RobotToQcReporterParser(object):

    @classmethod
    def add(cls, subparsers):
        desc = ('Reports Robot Framework test case results to Quality Center.')
        epilog = "Example: %prog -s 'Root\VGP\NG15.5\My Test Suite' rfcli_output/output.xml"
        subparser = subparsers.add_parser('robot2qc',
                                          help='report robot results to QC',
                                          description=desc,
                                          epilog=epilog,
                                          formatter_class=argparse.RawTextHelpFormatter)
        subparser.add_argument(dest="report",
                               help="Robot Framework's output.xml file to report", metavar="output.xml")
        mutex_group = subparser.add_mutually_exclusive_group(required=True)
        mutex_group.add_argument("-s", "--set", dest="testset",
                               help=("Path to QualityCenter test set where to report the results.\n"
                                     "E.g. 'Root\VGP\NG15.5\My Test Suite'"))
        mutex_group.add_argument("-i", "--set-id", dest="testset_id",
                               help="Numeric ID of the test set where to report the results.\nE.g. '1234'")
        subparser.add_argument("-r", "--release", dest="release",
                               help="Release to report.\nE.g. 'OSR+ H.5'")
        subparser.add_argument("-b", "--build", dest="build",
                               help="SW build to report.\nE.g. 'necc_24'")
        subparser.set_defaults(cmd=RobotToQcReporter)


class RobotToQcReporter(QcXmlHandler):

    def __init__(self):
        super(RobotToQcReporter, self).__init__()
        self.results = None

    def run(self, args):
        self.results = RobotResultParser(args.report).get_results()
        self._report(args.testset, args.testset_id, args.release, args.build)

    @staticmethod
    def _split_testset_argument(testset_input):
        Log.debug("Parsing test set '%s'" % testset_input)
        match = re.search(r'\\', testset_input)
        if not match:
            raise QcReporterException("Test set path must look like 'Root\\Folder\\...\\Test set name' "
                                      "and it must contain at least one path separator character ('\\')")
        testset_components = testset_input.rsplit('\\', 1)
        testset_path = testset_components[0]
        testset_name = testset_components[1]
        Log.debug("Looking for test set %s in path %s" % (testset_name, testset_path))
        return (testset_path, testset_name)

    def _report(self, testset_opt, testset_id_opt, release=None, build=None):
        Log.critical("Trying to connect QualityCenter...")
        # Log.info('Connected to QCXML version %s' % client.GetVersion())
        Log.critical("Validating data...")
        if testset_id_opt:
            testset_qcid = testset_id_opt
        else:
            testset_path, testset_name = self._split_testset_argument(testset_opt)
            try:
                testset_qcid = self.client.FindTestSet(testset_path, testset_name)
            except:
                testset_qcid = self.client.AddTestSet(testset_path, testset_name)
        already_added_cases = self.client.GetTestSetInstances(testset_qcid)
        Log.info('QC internal ID for the test set is "%s". It contains instances for %s test cases' %
                    (testset_qcid, len(already_added_cases)))
        results = []
        for result in self.results:
            # Extend result dicts with QC internal IDs for test cases
            try:
                test_case_id = result['test_case_id'].split()[0]
                qcid = self.client.FindTestCase(test_case_id)
                Log.info('QC internal ID for test case "%s" is "%s"' % (test_case_id, qcid))
                result['qcid'] = qcid
                qcstatus = "Passed" if result['status'] == "PASS" else "Failed"
                result['qcstatus'] = qcstatus
                results.append(result)
            except Exception, errmsg:
                Log.info("test case id <%s> error: %s"%(test_case_id, errmsg))
                
        Log.critical("Reporting results...")
        for r in results:
            Log.info('Reporting "%s" ("%s", QC: %s) as "%s"' %
                             (r['name'], r['test_case_id'], r['qcid'], r['qcstatus']))
            if r['qcid'] in already_added_cases:
                instance_qcid = already_added_cases[r['qcid']]
            else:
                instance_qcid = self.client.AddTestToTestSet(r['qcid'], testset_qcid)
            self.client.AddRunToTestSet(instance_qcid, testset_qcid, r['qcstatus'], release, build)
        Log.info("Source result [%s] -> uploaded result [%s]" % (self.results.__len__(), results.__len__()))
        Log.critical("Reporting completed")
