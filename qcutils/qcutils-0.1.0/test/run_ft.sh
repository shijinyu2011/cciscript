#!/bin/bash
#
# Very simple FT - has dependencies:
# - ~/.qcutilsrc must be configured
# - QC must have tested paths preconfigured
#

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

test_qcutils() {
  script="PYTHONPATH=.. ../qcutils/scripts/qcutilscli.py"
  verifyrc=0
  cmd="$script $@"
  echo "#################################################################"
  echo "Executing: \"$cmd\""
  time bash -c "$cmd"
  ret=$?
  if [ $ret -ne $verifyrc ]; then
    echo "FAILED, rc=$ret"
    exit 1
  fi
}

cd $DIR
test_qcutils addtc '"Subject/_RecycleBin_/qcutils-test"' QCUTILS_TEST_001 '"add tc to qc"'
test_qcutils addtc '"Subject/_RecycleBin_/qcutils-test"' QCUTILS_TEST_001 '"add tc to qc again, modify it"' --priority wont --req-id 2

tmpout=$(mktemp)
pybot --report NONE --log NONE --output $tmpout qcutils_report.robot
test_qcutils robot2qc -s '"Root\_RecycleBin_\qcutils-test\qcutils-test-set"' $tmpout
test_qcutils robot2qc -s '"Root\_RecycleBin_\qcutils-test\qcutils-test-set"' -r '"VGP 0.1"' -b 'vgp.1234.5678' $tmpout
rm -f $tmpout

echo "=== PASSED ==="
cd -
