#!/bin/bash
export OS_AUTH_URL=http://10.70.56.90:5000/v2.0
export OS_TENANT_ID=e3b91b99f7b449ebb58b1eb88a495851
export OS_TENANT_NAME="CCI-R-1"
export OS_PROJECT_NAME="CCI-R-1"
export OS_USERNAME="cci"
export OS_PASSWORD="cci"
export OS_REGION_NAME="RegionOne"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi

