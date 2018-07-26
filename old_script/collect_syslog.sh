#!/usr/bin/expect -f
# script to check instance status in openstack
# This script needs four argument to(s) connect to remote server:
# ipaddr = IP Addreess of instance
# user = USER of the instcne
# password = Password of for user
# For example:
# ./collect_syslog.sh 10.70.78.96 _rcpadmin RCP_owner /var/log/local/syslog
set ipaddr [lrange $argv 0 0]
set user [lrange $argv 1 1]
set password [lrange $argv 2 2]
set logfile [lrange $argv 3 3]

set timeout 30

spawn scp ${user}@${ipaddr}:${logfile}  ./logs/
expect {
    -re ".*sword.*" {send "${password}\r"}
    -re ".*Are you sure you want to continue connecting.*" {send "yes\r"
          expect -re ".*sword.*" {send "${password}\r"}
          }
   }
expect eof   
