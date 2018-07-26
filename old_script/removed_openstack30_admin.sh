#!/bin/bash
export OS_AUTH_URL=http://10.56.212.30:5000/v2.0
export OS_TENANT_ID=a8ca6c24992441e4acfb006c10005485
export OS_TENANT_NAME="htn"
export OS_USERNAME="admin"
export OS_PASSWORD='password'
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
