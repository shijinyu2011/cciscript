#!/bin/bash

if [ $# -ne 1 ]
then
  echo "This script switches the SVN URL and revision of the modules"
  echo "according to given CORR TAG. Give in the same folder where"
  echo "modules were checked out by checkout.py. Execute this script"
  echo "before setting the environment with setenv to get correct"
  echo "environment."
  echo
  echo "Usage: $0 <CORR_TAG>"
  echo "Example $0 R_QNCB.14.26.1_4"
  exit 1
fi

#R_QNCB.14.38.70_4

SVN_BASE="https://svne1.access.nsn.com"
CORR_TAG=$1

#IS_DEV_BUILD=`echo $CORR_TAG | grep -E "R_QNCBD\.[0-9]+\.[0-9]+\.[1-9][0-9]_[0-9]+"`

#if [[ $IS_DEV_BUILD == $CORR_TAG ]]
#then 
#  SCM_ERN="isource/svnroot/scm_ern/tags/mcRNC-main"
#  BASE_TAG=$CORR_TAG
#  SVN_URL=$SVN_BASE/$SCM_ERN/$CORR_TAG
#  echo "Dev build"
#else
  SCM_ERN="isource/svnroot/scm_rcp/tags"
  #BASE_TAG=`echo $CORR_TAG | sed "s/_[0-9]\+/\.1/"`
  BASE_TAG=``
  SVN_URL=$SVN_BASE/$SCM_ERN/$BASE_TAG/$CORR_TAG
  echo "Not dev build"
#fi

echo "Changing the modules to be same as in $SVN_URL"
echo

for D in *; do
    if [ -d "${D}" ]; then
        SVN_PROP=`svn pg svn:externals $SVN_URL | grep $D`
        REVISION=`echo $SVN_PROP | cut -d " " -f2`
        TARGET_SVN_URL=`echo $SVN_PROP | cut -d " " -f3`
        echo "Switch $D to $REVISION ${SVN_BASE}$TARGET_SVN_URL"
        cd $D
        svn switch ${SVN_BASE}$TARGET_SVN_URL
        svn up $REVISION
        cd ..
   fi
done
