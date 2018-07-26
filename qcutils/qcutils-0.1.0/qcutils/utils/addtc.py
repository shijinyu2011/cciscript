import argparse

from qcutils.log import Log
from qcutils.qchandler import QcRestHandler


class AddTestCaseParser(object):

    @classmethod
    def add(cls, subparsers):
        desc = ('Add / update a test case in Quality Center. Limitations:\n'
                ' - The test case path must exist in QC\n'
                ' - Any requirement to be linked must exist in QC\n'
                ' - Requirement mappings are _added_ not updated!\n')
        epilog = ('Example: %prog "Subject/_RecycleBin_/sandbox" "FT_SANDBOX_001" '
                  '"add a test case to sandbox" --priority wont')
        subparser = subparsers.add_parser('addtc',
                                          help='add/update a test case',
                                          description=desc,
                                          epilog=epilog,
                                          formatter_class=argparse.RawTextHelpFormatter)
        subparser.add_argument(dest="qc_path",
                               help=("Path to QualityCenter test case in 'Test Plan'. "
                                     "The path must exist in QC, is not created on the fly.\n"
                                     "e.g. 'Subject/VGP&LCC/cloudtaf_intro_20141103'"))
        subparser.add_argument(dest="tcid", type=cls.validate_tc_id_len,
                               help=("Test case ID, identical to test case name on robot side\n"
                                     "e.g. 'NECC_NTP_001'"))
        subparser.add_argument(dest="name", default="",
                               help=("Test case name, a very brief description of the case. "
                                     "Will be prefixed with the test case ID.\n"
                                     "e.g. 'verify all NTP services are up and running'"))
        subparser.add_argument("--priority", dest="priority",
                               help=("must/should/could/wont\n"
                                     "default: should"),
                               default='should')
        subparser.add_argument("--req-id", dest="requirement_id",
                               help="Requirement ID that the test case maps to.")
        subparser.set_defaults(cmd=AddTestCase)

    @classmethod
    def validate_tc_id_len(cls, tc_id):
        maxlen = 40
        if len(tc_id) > maxlen:
            raise argparse.ArgumentTypeError("Too long ID given, maximum length set by QC is %d" % maxlen)
        return tc_id


class AddTestCase(QcRestHandler):

    def run(self, args):
        qc_test_id = self.add_tc(args.qc_path, args.tcid, args.name, args.priority)
        if args.requirement_id:
            self.map_tc2req(qc_test_id, args.requirement_id)

    def add_tc(self, test_path, test_id, test_name, test_prio):
        parent_id = self.client.resolveTestFolderQcId(test_path)
        existing_test_id = self.client.getTestCaseByTCID(test_id, parent_id=parent_id, raise_on_empty_match=False)
        if existing_test_id:
            Log.info('test %s: id=%s already exists - updating' % (test_id, existing_test_id))
            self.client.updateTestCase(existing_test_id, parent_id, test_id, test_name, test_prio)
        else:
            Log.info('test %s: not existing - adding' % (test_id))
            existing_test_id = self.client.addTestCase(parent_id, test_id, test_name, test_prio)
        return int(existing_test_id)

    def map_tc2req(self, qc_test_id, requirement_id):
        coverage = self.client.getReqCoverageByTCID(qc_test_id)
        if requirement_id in coverage:
            Log.info('Requirement map already exists - no need to create')
        else:
            Log.info('Requirement map missing - creating')
            self.client.addReqCoverage(qc_test_id, requirement_id)
