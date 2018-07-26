#!/bin/bash
imagefile=$1
product=$2
product_lower_case=`echo ${product} | tr A-Z a-z`
imagename=`echo $imagefile|sed s/.tar.gz//g`
dns_maps=("gerrit.nsn-net.net:10.159.194.193" "hzgitv01.china.nsn-net.net:10.159.194.193" "gerrite1.ext.net.nokia.com:93.183.20.134")
dns_opt=""
for dns in ${dns_maps[@]}
do
        echo $dns
        dns_opt="$dns_opt --add-host=$dns"
done

for i in `docker ps -a|grep "2223->22\|2224->22\|cci_${product_lower_case}_"|cut -d " " -f1`;do
   echo $i
   echo "docker kill $i"
   docker kill $i
   echo "docker rm $i"
   docker rm $i
done

for old_docker in `docker images|grep cci_${product_lower_case}_|sed "s/[ \t]\+/ /g"|cut -d " " -f3`;do
   echo "remove old docker iamges"
   echo "docker rmi $old_docker"
   docker rmi $old_docker
done

echo "cat $imagefile | docker import - $imagename"
cat $imagefile | docker import - $imagename

ports="2223 2224"
for i in $(echo $ports);do
   cmd="docker run $dns_opt --privileged=true -d -v /McBED/sacks:/McBED/sacks -v /ephemeral/cBTS:/cBTS -p $i:22 $imagename /usr/sbin/sshd -D"
   echo "run cmd: $cmd"
   $cmd
   if [ $? -ne 0 ];then
         echo "run $cmd failed, exit"
         exit 1
   fi   
done     
rm -fr $imagefile

