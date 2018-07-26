#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..
pylint --rcfile $DIR/pylintrc qcutils -i y $@
cd -
