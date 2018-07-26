#!/bin/bash
set -e

[ -d "~/.ssh" ] && rm -rf ~/.ssh
cp -a cciscript/tosco_sshkey/.ssh ~/.ssh
chmod 400 ~/.ssh/id_rsa
mkdir -p docker_workspace
cd docker_workspace
rm -fr *
workdir=`pwd`
mkdir -p $workdir/convert

product=$1
product=${product:="vRNC"}
product_lower_case=`echo ${product} | tr A-Z a-z`

echo "############get base image"
triggerfile="https://gitlabe1.ext.net.nokia.com/ILCI/trigger/raw/master/cloudil/latest_ok_smoke_tested/cloudil_smk_ok_trigger.txt"
curl -k -s $triggerfile  -o trigger.txt 
cur_build_id=`cat trigger.txt | grep "^build_id" | sed 's/build_id=//g'`
image_path=`cat trigger.txt |grep -o "image_url=.*"|cut -d "=" -f2|sed "s/rcp.dynamic.nsn-net.net/10.56.118.71/g"`
if [ -f "$WORKSPACE/logs/build_id" ];then
    old_build_id=`cat $WORKSPACE/logs/build_id`
    echo "old_build_id=$old_build_id cur_build_id=$cur_build_id"
    if [[ "$old_build_id" == "$cur_build_id" && "$force" == "false" ]];then
        echo "$cur_build_id cloud il devel image has exist, skip !!!"
        exit 0
    fi
fi

echo "image path is ${image_path}"
image_pattern="CLOUD_IL_RNC.*-devel_.*qcow2"
imagename=`curl $image_path|grep -o ${image_pattern}|cut -d ">" -f2 | uniq`
docker_image_name=`echo $imagename|sed "s/.qcow2//g"`
echo "wget $image_path/$imagename -q -O $docker_image_name.qcow2"
# if echo $product|grep -q vRNC; then 
#    scp hzscm@10.56.118.71:/tosco/tosco/builds/RCP/$(echo ${image_path}|cut -d "/" -f4-)/$imagename ./$docker_image_name.qcow2 
# else
   [ -f $docker_image_name.qcow2 ] || wget $image_path/$imagename -O $docker_image_name.qcow2
# fi
echo "##########convert base image to docker image " 
yum install -y parted
qemu-img convert -f qcow2 -O raw $docker_image_name.qcow2 $docker_image_name.raw
offset=`parted $docker_image_name.raw -s unit b print|grep -A 1 "Start"|grep -v "Start"|cut -d " " -f3- |sed "s/ //g"|sed "s/B.*//g"`
mount -o loop,rw,offset=$offset $docker_image_name.raw $workdir/convert

cd $workdir/convert
# workaround for "Missing privilege separation directory: /var/empty/sshd"
if [ ! -h ./var/empty/sshd/etc/localtime ]; then
   mkdir -p ./var/empty/sshd/etc
   ln -s /etc/localtime ./var/empty/sshd/etc/localtime
fi
sudo tar -czf $workdir/$docker_image_name.tar.gz .
cd ..
sudo umount $workdir/convert
rm -fr *.qcow2 *.raw
rcpdockerimage=`echo CCI_${product}_$docker_image_name | tr A-Z a-z`

echo "############remove old docker images"
set +e
docker images | grep "$rcpdockerimage"
if [ $? -eq 0 ];then
  docker rmi $rcpdockerimage --force
fi
set -e

echo "############import base images"
cat $docker_image_name.tar.gz | docker import - $rcpdockerimage
rm -fr *.tar.gz


echo "############add ci tools to docker image"
git clone git@gitlabe1.ext.net.nokia.com:swd3ci/docker-image.git
cd docker-image

tool_root_url="http://distro.es-ka-s3-dhn-14.eecloud.nsn-net.net"
# tool_root_url="http://distro.s3-us-1.eecloud.nsn-net.net"
## for backup
bak_tool_root_url="http://eclipseupd.china.nsn-net.net/distro/tools"

wget -nv ${tool_root_url}/klocwork.tar.gz 
wget -nv ${tool_root_url}/tnsdlunit.tar.gz 
wget -nv ${tool_root_url}/auth.tar.gz 


sed -i "s/docker_image_for_cloudil/$rcpdockerimage/g" Dockerfile
docker build -t new_image .
docker tag new_image prime-local.esisoj70.emea.nsn-net.net/prime/cloudil-devel:latest
docker login -u x52chen -p AKCp2WXgcTLSujNn7EAg1u1ZuEPwWZvuPXoK2SkpyLEaGmMDqwT2VvuJHZheDP3U9bwv54Uw3 prime-local.esisoj70.emea.nsn-net.net
docker push prime-local.esisoj70.emea.nsn-net.net/prime/cloudil-devel:latest

[ -d $WORKSPACE/logs/ ] || mkdir -p $WORKSPACE/logs/
echo "$rcpdockerimage" > $WORKSPACE/logs/image.txt 
echo "$cur_build_id"  > $WORKSPACE/logs/build_id
echo "Success push $rcpdockerimage cloudil-devel image"
echo ""
echo ""
echo ">>>>>>>>>delete unused docker images<<<<<<<"
set +e
docker  ps -a | grep "Exited " |awk -F' ' '{print $1}' |xargs docker rm  -f
docker images -a | grep "<none>" | awk -F' ' '{print $3}' |xargs docker rmi -f
docker images -a | grep "$rcpdockerimage" | awk -F' ' '{print $3}' |xargs docker rmi -f
echo "delete unused docker images finish"