#!/bin/bash

set -x
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR
PYTHONPATH=$PWD nosetests -v --with-coverage --cover-branches --cover-erase ../qcutils
cd -

