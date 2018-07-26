#!/bin/bash

if [ $# -lt 2 ]; then
	echo "Syntax: $0 IP_ADDR USER ROOT_PASSWORD"
	echo "E.g. $0 192.168.1.1 root nokia123"
    exit -1
fi


me=`which $0`
me=`dirname $me`

#check if remote machine has our public key
ssh -oNumberOfPasswordPrompts=0 -oPasswordAuthentication=no -oStrictHostKeyChecking=no ${2}@${1} 'echo ""'
if [ $? -eq 0 ]
then
        echo "already register public key on ${1}"
        exit 0
fi

echo "upload public key to ${1}"
#rm -f $HOME/.ssh/known_hosts
#ssh-keygen -R ${1}
expect -f ${me}/upload_pubkey.sh ${1} ${2} ${3} "/${2}/.ssh/id_rsa.pub"

ssh -oNumberOfPasswordPrompts=0 -oPasswordAuthentication=no -oStrictHostKeyChecking=no ${2}@${1} 'echo ""'
if [ $? -eq 0 ]
then
        echo "registered public key on ${1} successfully"
        exit 0
fi

echo "failed to register public key on ${1} "
exit 1


