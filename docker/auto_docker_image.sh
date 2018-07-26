#!/bin/bash
set -e

ci_workspace=$(cd $(dirname "$0"); pwd)
mkdir -p docker_workspace
cd docker_workspace
rm -fr *
workdir=`pwd`
mkdir -p $workdir/convert

product=$1
product=${product:="vRNC"}
product_lower_case=`echo ${product} | tr A-Z a-z`
input_image_path=$2

echo "input image path is ${input_image_path}"

echo "############get base image"
if [ "`echo $product`" = "vRNC" ];then
   triggerfile="https://gitlabe1.ext.net.nokia.com/ILCI/trigger/raw/master/cloudil/latest_ok_smoke_tested/cloudil_smk_ok_trigger.txt"
   curl -k -s $triggerfile  -o trigger.txt 
   image_path=`cat trigger.txt |grep -o "image_url=.*"|cut -d "=" -f2|sed "s/rcp.dynamic.nsn-net.net/10.56.118.71/g"`
   image_pattern="CLOUD_IL_RNC.*-devel_.*qcow2"
else
   echo "$product not available , exit "
   exit 2
fi

if [ ! -z "${input_image_path}" ];then
   image_path=${input_image_path}
fi

echo "image path is ${image_path}"

imagename=`curl $image_path|grep -o ${image_pattern}|cut -d ">" -f2 | uniq`
docker_image_name=`echo $imagename|sed "s/.qcow2//g"`
if [ -f $docker_image_name.qcow2 ];then
   echo "$docker_image_name.qcow2 exist , skip download !!"
else
   echo "wget $image_path/$imagename -q -O $docker_image_name.qcow2"
   wget $image_path/$imagename -O $docker_image_name.qcow2
fi

echo "##########convert base image to docker image " 
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
for old_docker in `docker images|grep cci_${product_lower_case}_|sed "s/[ \t]\+/ /g"|cut -d " " -f3`;do
   echo "remove old docker iamges"
   docker rmi $old_docker
done

echo "############import base images"
cat $docker_image_name.tar.gz | docker import - $rcpdockerimage
rm -fr *.tar.gz


echo "############add ci tools to docker image"
git clone http://gerrit.nsn-net.net/prime_infra/docker-image
cd docker-image/rcpci-devel

tool_root_url="http://distro.es-ka-s3-dhn-14.eecloud.nsn-net.net"
# tool_root_url="http://distro.s3-us-1.eecloud.nsn-net.net"
## for backup
bak_tool_root_url="http://eclipseupd.china.nsn-net.net/distro/tools"

wget -nv ${tool_root_url}/klocwork.tar.gz 
wget -nv ${tool_root_url}/tnsdlunit.tar.gz 
wget -nv ${tool_root_url}/auth.tar.gz 


sed -i "s/docker_image_for_cloudil/$rcpdockerimage/g" Dockerfile
docker build -t $rcpdockerimage .
docker run --privileged=true -d -v /McBED/sacks:/McBED/sacks -p 2222:22 $rcpdockerimage /usr/sbin/sshd -D
contantid=`docker ps|grep "$rcpdockerimage"|cut -d " " -f1`
docker export $contantid > $rcpdockerimage.tar
gzip $rcpdockerimage.tar

echo "##########remove docker images"
newdockerimageid=`docker images|grep cci_${product_lower_case}_|sed "s/[ \t]\+/ /g"|cut -d " " -f3`
docker rm $contantid --force
docker rmi $newdockerimageid --force

if [ "`echo $product`" = "vRNC" ];then
    for i in `echo 02 03 04`;do
      dockerserver="hzrcpv$i.china.nsn-net.net"
      scp $ci_workspace/deploy.sh root@$dockerserver:/home/
      scp ./$rcpdockerimage.tar.gz root@$dockerserver:/home/
      ssh root@$dockerserver "cd /home; ./deploy.sh $rcpdockerimage.tar.gz $product"
      echo $dockerserver
    done
elif [ "`echo $product`" = "cBTS_two_sack" ];then
      dockerserver="10.157.20.92"
      #scp $ci_workspace/deploy.sh root@$dockerserver:/opt/
      #scp ./$rcpdockerimage.tar.gz root@$dockerserver:/opt/
      #ssh root@$dockerserver "cd /opt; ./deploy.sh $rcpdockerimage.tar.gz $product"
      $ci_workspace/deploy.sh $rcpdockerimage.tar.gz $product
      echo $dockerserver
fi

exit 0
