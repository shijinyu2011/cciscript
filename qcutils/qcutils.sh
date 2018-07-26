#!/bin/bash
#set -x
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

PKGDIR=$(find $DIR -maxdepth 1 -type d -name 'qcutils-*' | sort -n | tail -1)

PYTHONPATH=$PKGDIR:$PYTHONPATH python $PKGDIR/qcutils/scripts/qcutilscli.py "$@"
