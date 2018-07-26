#!/bin/bash
export OS_AUTH_URL=http://10.70.56.4:5000/v2.0
export OS_TENANT_ID=592ad15e62e248508d604cc445cbd1c5
export OS_TENANT_NAME="CCI-Monitor-3"
export OS_USERNAME="cci"
export OS_PASSWORD=cci
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi

