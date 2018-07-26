#!/bin/bash -e

tars="tars"
echo "PARENT_URL=$PARENT_URL"
echo "GERRIT_PATCHSET_REVISION=$GERRIT_PATCHSET_REVISION"
echo "JENKINS_URL=$JENKINS_URL"
if [[ ! "$JENKINS_URL" =~ "hzrcpciv01.china.nsn-net.net" ]];then
    is_eecloud="is_eecloud"
fi
new_imagename=" CIU_${product}_rcp-ci-r${GERRIT_PATCHSET_REVISION}_${subsystem}_watchdog-disabled"
if [ "`echo $product`" = "vRNC" ];then
    triggerfile="https://gitlabe1.ext.net.nokia.com/ILCI/trigger/raw/master/cloudil/latest_ok_smoke_tested/cloudil_smk_ok_trigger.txt"
    curl -k -s $triggerfile  -o trigger.txt  
   image_path=`cat trigger.txt |grep -o "image_url=.*"|cut -d "=" -f2|sed "s/rcp.dynamic.nsn-net.net/10.56.118.71/g"`
   image_pattern="CLOUD_IL_RNC.*-ci_.*qcow2"
else
    echo "$product not available, exit"
    exit 2
fi
imagename=`curl ${image_path}|grep -o ${image_pattern}|cut -d ">" -f2`
echo "wget ${image_path}/${imagename} -q -O ${new_imagename}"
wget ${image_path}/${imagename} -q -O ${new_imagename}

chmod +x cciscript/image/image_patch.sh
echo "cciscript/image/image_patch.sh $new_imagename $tars $is_eecloud"
./cciscript/image/image_patch.sh $new_imagename $tars $is_eecloud
./cciscript/image/upimage.sh $new_imagename $new_imagename $is_eecloud
rm -fr *
