import sys
sys.path.append('../common')
from mail import MailServer
import requests
import json
import logging
from common_func import get_logger
import argparse
from config import CCI_TEAM_MAIL

logger = get_logger('OamMailSender')



class OamMailSender(object):

    def __init__(self, **kwds):
        self.job_name = kwds.get('job_name', None)
        self.build_num = kwds.get('build_num', None)
        self.build_url = kwds.get('build_url', None)
        self.status = kwds.get('status', None)
        self.phase = kwds.get('phase', None)
        self.msg = kwds.get('msg',None)

    def send_mail(self, for_testing=False, send_to_self=False):
        sender = self.get_sender()
        receiver = self.get_receiver()
        if self.msg:
            message=self.msg
        else:
            message = self.get_mail_content()
        subject = self.get_subject()
        if send_to_self:
            cc_receivers = sender
        else:
            cc_receivers = ''
        logger.debug('''
        Sender: %s
        Receiver: %s
        messge:%s
        subject: %s
        ''' % (sender, receiver, message, subject))
        if for_testing:
            receiver = ['yongting.zhang@nokia.com']
        ms = MailServer()
        ms.send_mail(sender, ';'.join(receiver), message, subject, cc_receivers)

    def get_subject(self):
        return 'OAM Job %s %s %s' % (self.job_name, self.phase, self.status)

    def get_receiver(self):
        build_api_url = '%s/api/json' % self.build_url
        receivers = []
        r = requests.get(build_api_url)
        if r.status_code != 200:
            logger.error('Could not get jenkins build json data from %s\n Error is %s' % (build_api_url, r.text))
        else:
            j_d = json.loads(r.text)
            receivers = self._get_gerrit_committer(j_d)
            if not receivers:
                receivers = self._get_svn_committer(j_d)
        if not receivers:
            receivers = [CCI_TEAM_MAIL]
        return receivers

    def _get_gerrit_committer(self, json_data):
        actions = json_data['actions']
        parameters = {}
        for a in actions:
            if a.has_key('parameters'):
                parameters = a['parameters']
                break
        for parameter in parameters:
            p_name = parameter['name']
            p_value = parameter['value']
            if p_name == 'GERRIT_EVENT_ACCOUNT_EMAIL':
                committer = p_value
                return [committer]
        return None

    def _get_svn_committer(self, json_data):
        users = []
        items = json_data['changeSet']['items']
        for item in items:
            users.append(item['user'])
        return [user + '@nokia.com' for user in users]

    def get_mail_content(self):
        content = '''
        OAM job : %s<br/>
        job link: %s<br/>
        phase : %s <br/>
        build status: %s<br/>

        ''' % (self.job_name, self.build_url, self.phase, self.status.capitalize())
        return content

    def get_sender(self):
        return CCI_TEAM_MAIL


def create_parser():
    parser = argparse.ArgumentParser(description='OAM Mail Sender')
    parser.add_argument('-v', '--verbose', action='store_true', help='set debug mode')
    parser.add_argument('-j', '--job', help='jenkins job name')
    parser.add_argument('-b', '--build', help='jenkins build url')
    parser.add_argument('-p', '--phase', help='oam cci phase')
    parser.add_argument('-s', '--status', help='phase status, success or fail.')
    parser.add_argument('-g', '--gerrit', help='gerrit ref, used to distinguish svn or gerrit')

    return parser


def test():
    build_url = 'http://hzacivm01.china.nsn-net.net:8080/user/yongtzha/my-views/view/oam_test/job/oam_trunk_cci_raktor-test/1/'
    oam_sender = OamMailSender()
    print oam_sender.get_receiver(build_url)

if __name__ == '__main__':
    parser = create_parser()
    # args = parser.parse_args('-j oam_trunk_cci_raktor-test -b http://hzacivm01.china.nsn-net.net:8080/user/yongtzha/my-views/view/oam_test/job/oam_trunk_cci_raktor-test/1/ -s Fail -p compilaton -v'.split())
    args=parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.job or not args.build or not args.phase or not args.status:
        logger.error('Job name , build url ,phase or status can not be empty')
        parser.print_help()
        sys.exit(110)

    if args.gerrit:
        phase = 'gerrit-%s' % args.phase
    else:
        phase = 'svn-%s' % args.phase

    mail_sender = OamMailSender(**{'job_name': args.job, 'build_url': args.build, 'phase': phase, 'status': args.status})
    mail_sender.send_mail()

    sys.exit()
