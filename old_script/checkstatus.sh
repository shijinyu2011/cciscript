#!/usr/bin/expect -f
# script to check instance status in openstack
# This script needs four argument to(s) connect to remote server:
# ipaddr = IP Addreess of instance
# user = USER of the instcne
# password = Password of for user
# For example:
# ./checkstatus.sh 10.70.78.96 _nokadmin Nokia123
set ipaddr [lrange $argv 0 0]
set user [lrange $argv 1 1]
set password [lrange $argv 2 2]
set timeout 30
   spawn ssh ${user}@${ipaddr}
   expect {
      -re ".*Are you sure you want to continue connecting.*" {send "yes\r"
          expect -re ".*sword.*" {send "${password}\r"}
          }
      -re ".*sword:.*" {send "${password}\r"
            }
   }
expect {
   -re ".*sword:.*" {send "\003\r"}
   -re "_nokadmin@UI-0.*>" {send "show has state managed-object /*/*\r"
     set i 1
     while {$i} {
       expect {
          -re ".*--More--.*" {send "\r"}
          -re ".*_nokadmin@UI-0.*" {
           set i 0
           send "\r"}
       }
     sleep 0.2
   }
    send "exit\r"

    }
}
