#!/bin/bash

#image: local image name
#image_name: openstack image name
image=$1
image_name=$2
is_eecloud=$3
server_ip=10.68.165.226
USER=root
subsystemdir=/data/www-root/cloudil/$subsystem/images

generateSshKey(){
    [ -d "~/.ssh" ] && rm -rf "~/.ssh"
    cp -a ${WORKSPACE}/cciscript/tosco_sshkey/.ssh ~/.ssh
    chmod 400 ~/.ssh/id_rsa
    chmod 400 ~/.ssh/id_rsa_hale
}

if test $is_eecloud ;then
    generateSshKey
fi
#fix bugs: 
newimage=$image'_'`date +%Y%m%d%H%M%S`
ssh $USER@$server_ip "[ ! -d $subsystemdir ] && mkdir -p $subsystemdir;"
ssh $USER@$server_ip "cd $subsystemdir; rm -f CI*"
echo "scp ./$image $USER@$server_ip:$subsystemdir/${newimage}.qcow2"
scp $image $USER@$server_ip:$subsystemdir/${newimage}.qcow2
if [ $? != 0 ];then
    echo "scp image to server failed"
    exit 1
fi
ssh $USER@$server_ip "cd $subsystemdir;md5sum $newimage.qcow2 > $newimage.md5sum"
