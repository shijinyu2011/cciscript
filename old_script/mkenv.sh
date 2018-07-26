#!/bin/bash
rm -fr logs/*
rm -fr errlogs/*
mkdir -p logs
mkdir -p errlogs
export log_folder=${WORKSPACE}/logs
export errlog_path=${WORKSPACE}/errlogs
export configurefile=`echo $heat_template|sed "s/.*\///g"`
rm -fr $configurefile
wget $heat_template -O $configurefile
export heat_operator="cciscript/heat_operator.py"
export CASEPATH="${WORKSPACE}/SS_RCPCI"
export testbranchname="master" 
export git_dir_RCPCI="${WORKSPACE}/SS_RCPCI/.git"
export work_tree_RCPCI="${WORKSPACE}/SS_RCPCI"
