#!/usr/local/bin/expect
# Expect script to supply root/admin password for remote ssh server
# and execute command.
# This script needs three argument to(s) connect to remote server:
# ipaddr = IP Addreess of remote UNIX server, no hostname
# password = Password of remote UNIX server, for root user.
# For example:
#  ./sshlogin password 192.168.1.11 /home/eclipse
set ipaddr [lrange $argv 0 0]
set user [lrange $argv 1 1 ]
set password [lrange $argv 2 2]
set keypath [lrange $argv 3 3]
set timeout -1

# now connect to remote UNIX box (ipaddr) with given command to execute
spawn /usr/bin/scp -q -o StrictHostKeyChecking=no $keypath $user@$ipaddr:~/hudson_pub_key
match_max 100000
# Look for passwod prompt
expect "*?assword:*"
# Send password $password
send -- "$password\r"
# send blank line (\r) to make sure we get back to gui
send -- "\r"
expect eof

spawn /usr/bin/ssh -o StrictHostKeyChecking=no $user@$ipaddr "cat ~/hudson_pub_key >> ~/.ssh/authorized_keys"
match_max 100000
# Look for passwod prompt
expect "*?assword:*"
# Send password $password
send -- "$password\r"
# send blank line (\r) to make sure we get back to gui
send -- "\r"
expect eof

