#!/bin/bash

script_dir=$(cd $(dirname $0) && pwd)
gerrit_py="$script_dir/../common/gerrit.py"
echo "[info]current sub name is ${GERRIT_PROJECT}"

if [ -z "${GERRIT_CHANGE_ID}" ];then
    echo "No gerrit change id found. Skip"
    exit 0
fi

if [[ -z "${build_result}" || -z "$BUILD_URL" ]];then
  echo "no build result"
  exit 0
fi
message="Promote Result ${build_result}: ${BUILD_URL}"
send_mail(){
    mailto="$GERRIT_CHANGE_OWNER_EMAIL"
    ccto="$GERRIT_EVENT_ACCOUNT_EMAIL"
    if [ ! -z "$mailto" ];then
        echo "send_mail to $mailto cc $ccto"
        echo -e "$message  \ngerrit change:$GERRIT_CHANGE_URL" | mail -s "${GERRIT_PROJECT} $GERRIT_BRANCH Promote ${build_result}" -c $ccto  $mailto
    fi
}
push_info_to_gerrit(){
    echo "python ${gerrit_py} review -m \"$message\" -c ${GERRIT_CHANGE_ID}"
    result=$(python ${gerrit_py} review -m "$message" -c ${GERRIT_CHANGE_ID}) 
}
send_mail
push_info_to_gerrit