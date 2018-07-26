#!/bin/bash -e
BRANCH=${GERRIT_BRANCH}
git archive --format=tar --remote=git@gitlabe1.ext.net.nokia.com:IL_SCM/common_il.git master commonil_gitrepo.lst | tar -xO -f - > gitrepo.list
if [ ! -n "${GERRIT_PROJECT}" ]; then
  echo "gerrit project is null, please trigger with gerrit"
  exit 1
fi

if [ "${GERRIT_BRANCH}" = "$cloudVT" ];then
   type="cloud"
else
   type=il
   cat gitrepo.list |grep "${GERRIT_PROJECT} " && type=common
fi
echo "type=$type" > $WORKSPACE/property
cat $WORKSPACE/property

echo "------------------post message to gerrit page------------------"
gerrit_url="https://$GERRIT_SERVER/a/changes/$GERRIT_CHANGE_ID/revisions/current/review"
gerrit_post="{\"message\": \"Promote Start: $BUILD_URL\", \"labels\": {}}"
set +e
curl -s -k -u  hzci:b2a6eefb -H "Content-Type: application/json" -X POST --data "$gerrit_post" "$gerrit_url"
exit 0