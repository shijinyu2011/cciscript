#!/bin/bash
export OS_AUTH_URL=http://10.70.78.190:5000/v2.0
export OS_TENANT_ID=fed5d117960342279d92ba0117324ad5
export OS_TENANT_NAME="admin"
export OS_USERNAME="admin"
export OS_PASSWORD="password"
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
