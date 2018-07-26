import string
import random
import os, time, sys
import syslog
import datetime
import socket
from syslog import (LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR,
                   LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG)

LOG_NAME = "/var/log/local/syslog"


def string_message_generator(size=2000, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_generated_message_and_send_to_journal():
    generated_message = string_message_generator()
    syslog.syslog(syslog.LOG_ERR, generated_message)
    return generated_message

def get_application_name():
    app_name = sys.argv[0]
    application_split = app_name.split("/")
    application_name = application_split[2]
    return application_name

def get_journal_priority(lrandom_message):
    os.system("journalctl -o verbose MESSAGE=" + lrandom_message + " | grep 'PRIORITY' | awk '{ print $1} ' > /tmp/priority ")
    priority = {"0":"emerg", "1":"alert", "2":"crit", "3":"err", "4":"warning", "5":"notice", "6":"info", "7":"debug"}
    with open("/tmp/priority", "r") as mypriorityfile:
        priority_data = mypriorityfile.read().replace("\n" , "")
    priority_journal = priority_data.split("=")
    priority_levelno = priority_journal[1]
    journal_priority_number = priority[priority_levelno]
    mypriorityfile.close()
    return journal_priority_number

def get_journal_microseconds(lrandom_message):
    os.system("journalctl -o verbose MESSAGE=" + lrandom_message + " | grep '\[s=' | awk ' {print $3, $4} ' > /tmp/time")
    with open("/tmp/time", "r") as myfile:
        data = myfile.read().replace("\n", "")
    myfile.close()
    new_data = data.split(" ")
    journal_variable_log = new_data[0]
    journal_time = datetime.datetime.strptime(journal_variable_log, '%H:%M:%S.%f')
    journal_hours = journal_time.hour
    journal_minutes = journal_time.minute
    journal_seconds = journal_time.second
    journal_microseconds = journal_time.microsecond
    journal_total_microseconds = 60 * 60 * 1000000 * journal_hours + 60 * 1000000 * journal_minutes + 1000000 * journal_seconds + int(journal_microseconds)
    return journal_total_microseconds

def main(args):
    syslog.openlog()
    #Get random message, PID, hostname and application name to concatenate them into the string_message
    random_message = get_generated_message_and_send_to_journal()
    process_id  = os.getpid()
    hostname = socket.gethostname()
    name_of_application = get_application_name()
    journal_priority_no = get_journal_priority(random_message)
    journal_total_microsec = get_journal_microseconds(random_message)
    string_message =  journal_priority_no + " " + str(hostname) + " " + name_of_application  + "[" + str(process_id) + "]" + ": " + random_message
    variable_log = ""
    message_exists_in_syslog = 0
    microseconds_difference_acceptable = False
    time.sleep(2)
    #testlog = open_readonly(LOG_NAME)
    with open(LOG_NAME, "r") as testlog:
        for line in testlog:
            if string_message in line:
                message_exists_in_syslog +=1
                newline = line.split(" ")
                variable_log = newline[2]
                #the datetime is stripped according to the following format,in order to get hour,minute,seconds and convert them to microseconds.
                syslog_split_time = datetime.datetime.strptime(variable_log, '%H:%M:%S.%f')
                syslog_hours = syslog_split_time.hour
                syslog_minutes = syslog_split_time.minute
                syslog_seconds = syslog_split_time.second
                syslog_microseconds= syslog_split_time.microsecond
                syslog_total_microseconds = 60 * 60 * 1000000 * syslog_hours +  60 * 1000000 * syslog_minutes + 1000000 * syslog_seconds + syslog_microseconds
	        total_difference_in_microseconds = syslog_total_microseconds - journal_total_microsec
	        print "Total difference in microseconds between journal timestamp and syslog timestamp is: " + str(total_difference_in_microseconds)
                #see the documentation on robot test case, for why this amount of difference in microseconds is needed
                if total_difference_in_microseconds < 350:
                    print "times are almost identical, journal log has passed to syslog"
                    microseconds_difference_acceptable = True
	        else:
                    print "times are different, some error occured during journal writing to syslog"
                    sys.exit(3)
    testlog.close()
    syslog.closelog()
    if message_exists_in_syslog == 1 and microseconds_difference_acceptable:
        print "string message was found in syslog"
        sys.exit(0)
    elif message_exists_in_syslog == 0:
	print "string_message was not found in any line of the syslog file"
	sys.exit(1)
    elif message_exists_in_syslog >= 2:
        print "duplicate entries of string message were found inside syslog"
        sys.exit(2)
if __name__ == '__main__':
    main(sys.argv[1:])
