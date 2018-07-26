#!/bin/bash
templatefile=$1
publicExtnet=$2
zone=$3
echo "modify template file"
n1=`grep -A 4 -n "ext_net_id:" $templatefile|grep default:|cut -d"-" -f1`
sed -i "${n1} s/:.*/: $publicExtnet/g" $templatefile
n2=`grep  -n "UI-0_availability_zone:" $templatefile|cut -d ":" -f1`
sed -i "$n2,$((n2+15)) s/default:.*/default: \"$zone\"/g" $templatefile

sed -i "s/\\t//g" $templatefile
