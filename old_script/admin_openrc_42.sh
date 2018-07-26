#!/bin/bash
export OS_AUTH_URL=http://10.70.78.42:5000/v2.0
export OS_TENANT_ID=c767de371a1b47e1b414a5ebdd61df32
export OS_TENANT_NAME="DEV1"
export OS_USERNAME="admin"
export OS_PASSWORD="password"
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
