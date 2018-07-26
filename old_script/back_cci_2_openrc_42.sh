#!/bin/bash
export OS_AUTH_URL=http://10.70.78.42:5000/v2.0
export OS_TENANT_ID=a2e8ad70900249139bff3133b8710095
export OS_TENANT_NAME="CCI-W-2"
export OS_USERNAME="cci"
export OS_PASSWORD="cci"
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
