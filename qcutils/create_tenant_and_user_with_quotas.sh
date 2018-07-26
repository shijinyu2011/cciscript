#!/bin/bash
# 
# Script to create new tenant and user for openstack with quota that suits for CI testing.
# Enables to have several target environments in same Openstack environment.

TENANT_NAME="$1"
TENANT_DESCRIPTION="Tenant $1 for user $2"
USER_NAME="$2"
USER_PASSWORD="$3"
USER_EMAIL="$4"

QUOTA_INSTANCES=8
QUOTA_CORES=8
QUOTA_RAM=16384
QUOTA_GIGABYTES=100
QUOTA_VOLUMES=12


usage()
{
   echo -e "\n  Script to create new tenant and user for openstack. Heat yaml support for keystone comes in kilo release."
   echo -e "\n  Usage:"
   echo -e "\t$0 <tenant name> <username> <user password> <user email>\n"
   echo "  Example:"
   echo -e "\t$0 ci_project ci_user rastre1 sami.pesonen@nokia.com\n"
}

cleanup()
{
keystone tenant-delete ${TENANT_NAME}
keystone user-delete ${USER_NAME}
}

#main

if [ "$1" == "" ] || [ "$2" == "" ] ||  [ "$3" == "" ] ||  [ "$4" == "" ]; then
	usage
	exit 1
fi

keystone tenant-create --name ${TENANT_NAME} --description "${TENANT_DESCRIPTION}"
tenant_id=`keystone tenant-list | awk -v jou="$TENANT_NAME" '$0 ~ jou {print $2}'`
keystone user-create --name ${USER_NAME} --tenant ${tenant_id} --pass ${USER_PASSWORD} --email ${USER_EMAIL} --enabled true
keystone user-role-add --user ${USER_NAME} --role admin --tenant ${tenant_id}
keystone user-role-add --user ${USER_NAME} --role heat_stack_owner --tenant ${tenant_id}
user_id=`keystone user-list | awk -v jou2=${USER_NAME} '$0 ~ jou2 {print $2}'`

## quota volume 12, core amount 8, mem 16384, volume size 100GB
nova quota-update --user ${user_id} --instances ${QUOTA_INSTANCES} --cores ${QUOTA_CORES} --ram ${QUOTA_RAM} ${tenant_id}
nova quota-show --user ${user_id} --tenant ${tenant_id}
cinder quota-update --gigabytes ${QUOTA_GIGABYTES} --volumes ${QUOTA_VOLUMES} ${tenant_id}

exit 0
