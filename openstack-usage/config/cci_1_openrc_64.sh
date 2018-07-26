#!/bin/bash
export OS_AUTH_URL=http://10.70.56.64:5000/v2.0
export OS_TENANT_ID=659e4eb1e5994fddbce7c2f2ae672fae
export OS_TENANT_NAME="CCI-Monitor-1"
export OS_USERNAME="cci"
export OS_PASSWORD=cci
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi

