'''
Created on 2012-8-1

@author: yongtzha
'''
from email.MIMEText import  MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import  Utils,Encoders
from email.header import Header
import mimetypes
import smtplib
import string
import socket

MAIL_SERVER_LIST=["10.135.40.19:25", "mail.emea.nsn-intra.net"]
class MailServer:

    def __init__(self):
        self.server_list =MAIL_SERVER_LIST

    def send_mail(self,sender,receivers,message,subject,ccreceivers='',attatchments=[]):
        def attachment(filename):
            fd=open(filename,'rb')
            mimetype,mimeencoding=mimetypes.guess_type(filename)
            if mimeencoding or (mimetype is None):
                mimetype='application/octet-stream'
            maintype,subtype=mimetype.split('/')
            if maintype == 'text':
                retval = MIMEText(fd.read().encode('utf-8'),_subtype=subtype,_charset='utf-8')
            else:
                retval = MIMEBase(maintype,subtype)
                retval.set_payload(fd.read())
                Encoders.encode_base64(retval)
            retval.add_header('Content-Disposition','attachment',filename=filename)
            fd.close()
            return retval

        msg=MIMEMultipart()
        if isinstance(receivers,(str,unicode)):
            t_receivers=string.split(receivers,";")+string.split(ccreceivers,';')
            msg['To'] = receivers
            msg['CC'] = ccreceivers
        else:
            t_receivers=receivers.extend(ccreceivers)
            msg['To'] = ';'.join(receivers)
            msg['CC'] = ';'.join(ccreceivers)
        msg['From'] = sender
        msg['Subject'] = Header(subject,'utf-8')
        msg['Date'] = Utils.formatdate(localtime=1)
        msg['Message-ID'] = Utils.make_msgid()

        body=MIMEText(message,_subtype='html',_charset='utf-8')
        msg.attach(body)
        for filename in attatchments:
            msg.attach(attachment(filename))

        smtp = smtplib.SMTP()
        for server in self.server_list:
            print 'Connecting to mail server %s'%server
            try:
                smtp.connect(server)
                smtp.sendmail(sender,t_receivers,msg.as_string())
                print "Mail has been sent out."
                smtp.quit()
                break
            except smtplib.SMTPException,ex:
                continue
            except socket.error, se:
                print 'connection error: %s' %str(se)
                continue

if __name__ == "__main__":
    sender='yongting.zhang@nokia.com'
    receiver='yongting.zhang@nokia.com'
    message=" mail"
    subject="test "''
    ms=MailServer()
    ms.send_mail(sender,receiver,message,subject)
