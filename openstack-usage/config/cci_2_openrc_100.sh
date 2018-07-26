#!/bin/bash
export OS_AUTH_URL=http://10.70.56.100:5000/v2.0
export OS_TENANT_ID=9b4b7486d1d145aaa73cc893382afe28
export OS_TENANT_NAME="CCI-Monitor-2"
export OS_USERNAME="cci"
export OS_PASSWORD=cci
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi

