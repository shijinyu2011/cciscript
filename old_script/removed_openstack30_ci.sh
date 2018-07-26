#!/bin/bash
export OS_AUTH_URL=http://10.56.212.30:5000/v2.0
export OS_TENANT_ID=696d2036e881468aa51e4763118e4d19
export OS_TENANT_NAME="ci"
export OS_USERNAME="ci"
export OS_PASSWORD="ci"
export OS_REGION_NAME="RegionOne"
export publicExtnet="43b59dc4-c3b2-42b2-bbe9-f193068639d5"
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
