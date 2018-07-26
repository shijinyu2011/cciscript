#!/bin/bash
#./image_patch_qcow2 $imagename $tars_folder 
#imagename: image name
#tars_folder:tars folder
#isdocker:if docker container or not

imagename=$1
tar_folder=$2
isdocker=$3
subsystems=`ls ${tar_folder}/*{.tar.xz,.rpm}|cut -d"-" -f1|sed "s#.*\/##g"|uniq`
mymount=RCP_IMAGE
rm -fr $mymount
mkdir $mymount

echo "subsystems to patch:$subsystems"

removeoldfiles()
{
 configurefile=$1
 mymount=$2
 for i in `cat $configurefile`;do
   if test -f $mymount/$i ;then
      echo "remove $mymount/$i "
      rm -fr $mymount/$i
   fi
 done
}

patchtars()
{
 mymount=$1
 tars_folder=$2
 cd $mymount
 for tar_file in `ls ../${tars_folder}/*{.tar.xz,.rpm}|grep -v "\-devel\-"`;do
   echo "extract ${tar_file}"
   for i in `tar xvf ${tar_file} || (rpm2cpio ${tar_file} | cpio -di && rpm2cpio ${tar_file} | cpio -t)`;do
      if test -f $i;then 
        chmod 755 $i
      fi
    done
   #tar -xvf ${tar_file};
 done
cd -
}

upgradeRPMs()
{
    mymount=$1
    tars_folder=$2
    tars_in_new_root="${mymount}/tmp/tars"
    rm -rf ${tars_in_new_root} && mkdir -p ${tars_in_new_root} && cp -rf ${tars_folder}/*.* ${tars_in_new_root}
    cmd='ls /tmp/tars/*.rpm | grep -v "\-devel\-"'
    for tar_file in `sudo -E chroot ${mymount} sh -c "$cmd"`;do
        cmd="rpm -Uvh --nodeps --force ${tar_file}"
        sudo -E chroot $mymount sh -c "$cmd"
    done
    rm -rf ${tars_in_new_root}
}

postPatchActions()
{
    mymount=$1

    cmd="cd /opt/nokia/configure/sh/ && (ls | grep -i finalize | xargs -I {} echo excute script {});cd -"
    sudo -E chroot $mymount sh -c "$cmd"
    cmd="cd /opt/nokia/configure/sh/ && (ls | grep -i finalize | xargs -I {} sh {});cd -"
    # cmd="cd /opt/nokia/configure/sh/ &&(for tmp_file in `ls | grep -i finalize`;do echo excute $tmp_file;sh $tmp_file;done);cd -"
    sudo -E chroot $mymount sh -c "$cmd"
} 

echo "`pwd`: unpack image....."

if test -z $isdocker; then 
	modprobe nbd max_part=16
	
	for nbd in `ls /dev/nbd* | grep -v /dev/nbd.*p1`; do
	    echo "qemu-nbd -c $nbd $imagename"
	    qemu-nbd -c $nbd $imagename
	    if [ $? -eq 0 ]; then
	            dev=$nbd
	            break
	    fi
	done
	
	partprobe $dev

	echo "mount ${dev}p1 $mymount"
	mount ${dev}p1 $mymount
else
   temp_raw=temp.raw
   yum install -y parted # workround as the docker container do not have parted
   qemu-img convert -f qcow2 -O raw $imagename $temp_raw
   offset=`parted $temp_raw -s unit b print|grep -A 1 "Start"|grep -v "Start"|cut -d " " -f3- |sed "s/ //g"|sed "s/B.*//g"`
   mount -o loop,rw,offset=$offset $temp_raw $mymount
fi

echo "remove old tars...."
for subsystem in `echo "$subsystems"`;do
  configurefiles=`find $mymount| grep "contents\/$subsystem\-"`
  for configurefile in `echo "$configurefiles"`;do
    echo "removeoldfiles $configurefile"
    removeoldfiles $configurefile $mymount
    rm -fr $configurefile
  done
done

echo "patch new tars...."
patchtars $mymount ${tar_folder}

echo "upgrade RPMs...."
upgradeRPMs $mymount ${tar_folder}

echo "execute finalize scripts...."
postPatchActions $mymount

echo "`pwd`: umount images and delete ${dev}"
umount $mymount
if test -z $isdocker; then 
	qemu-nbd -d ${dev}
else
   qemu-img convert -c -f raw -O qcow2  -o compat=0.10 $temp_raw $imagename
fi   
rm -rf $mymount