#!/bin/bash

for f in '../cci_1_openrc_64.sh' ; do
    source $f
    echo $OS_AUTH_URL
    python nova_compute.py
done