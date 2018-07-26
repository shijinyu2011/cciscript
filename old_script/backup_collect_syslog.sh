#!/usr/bin/expect -f
# script to check instance status in openstack
# This script needs four argument to(s) connect to remote server:
# ipaddr = IP Addreess of instance
# user = USER of the instcne
# password = Password of for user
# For example:
# ./collect_syslog.sh 10.70.78.96 _nokadmin Nokia123 10.159.218.20 /opt/RCP/jenkins/workspace/SS_RCPMsg_FT/cciscript/
set ipaddr [lrange $argv 0 0]
set user [lrange $argv 1 1]
set password [lrange $argv 2 2]
set ftserver [lrange $argv 3 3]
set logpath [lrange $argv 4 4]

set ftserveruser "root"
set ftserverpasswd "Temp1234"
set logfiles "/var/log/local/syslog /var/log/local/debug /var/log/fsaudit/auth.log /var/log/fsaudit/alarms"

set timeout 300
set cmd_prompt "bash.*$"

spawn ssh ${user}@${ipaddr}
expect {
    -re ".*sword.*" {send "${password}\r"}
    -re ".*Are you sure you want to continue connecting.*" {send "yes\r"
          expect -re ".*sword.*" {send "${password}\r"}
          }
   }   
expect {
   -re "_nokadmin@UI-0.*>" {send "shell bash full\r"}
   }
expect {   
   -re ".*Are you sure you want to proceed.*" {send "Y\r"}
   }
expect {   
   -re "${cmd_prompt}" {send "scp ${logfiles} ${ftserveruser}@${ftserver}:${logpath}\r"}
   }
expect {
   -re ".*Are you sure you want to continue connecting.*" {
         send "yes\r"
         expect "*assword:*" { send "${ftserverpasswd}\n"}
         }
   -re ".*assword.*" {send "${ftserverpasswd}\r"}
   }

expect {
   -re "${cmd_prompt}" {send "exit\r"}
   }

