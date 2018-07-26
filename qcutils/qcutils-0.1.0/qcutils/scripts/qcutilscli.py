#!/usr/bin/env python

import sys
import argparse

from qcutils.log import Log
from qcutils.exception import QcUtilsException, QcUtilsDetailedException
from qcutils.utils.addtc import AddTestCaseParser
from qcutils.utils.robot2qc import RobotToQcReporterParser


class QcUtilsParser(object):

    def __init__(self):
        self.subparsers = None

    def parse_args(self, args):
        desc = ('Quality Center command line utilities. '
                'Part of the configuration, like QC server URL, username and password '
                'must be stored in $HOME/.qcutilsrc. ')
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument('-v', action="count", dest="verbosity",
                            help="Verbosity. Give -v option many times to be more verbose")
        self.subparsers = parser.add_subparsers()
        #--- Add any new utilities here ---
        self.add_subparser(AddTestCaseParser)
        self.add_subparser(RobotToQcReporterParser)
        return parser.parse_args(args)

    def add_subparser(self, subparser):
        subparser.add(self.subparsers)


class QcUtilsRunner(object):

    def main(self, args=None):
        args = QcUtilsParser().parse_args(args)
        Log.set_logging(args.verbosity)
        Log.debug('args:%s' % (args))
        try:
            command = args.cmd()
            command.initialize_client()
            command.run(args)
            self._exit(0)
        except QcUtilsDetailedException as e:
            Log.critical('\n\n----- Start error trace -----\n%s\n----- End error trace -----\n' % e.detail)
            Log.critical('Error: "%s"' % e)
            Log.critical('See stack trace above for more details')
            self._exit(1)
        except QcUtilsException as e:
            Log.critical('Error: "%s"' % e)
            self._exit(1)

    @staticmethod
    def _exit(rc):
        sys.exit(rc)


if __name__ == "__main__":
    QcUtilsRunner().main()
