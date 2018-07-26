import requests
import time
import argparse
import sys
from send_mail import OamMailSender
sys.path.append('../common')
from common_func import get_logger
import logging
import config
import json
from  multiprocessing import Pool

logger = get_logger('OamSMT')


def get_smt_result(task_id):
    url = config.SMT_RESULT_API
    payload = {'id': task_id}
    is_success = False
    smt_job_url = ''
    task_link = ''
    while True:
        r = requests.get(url, params=payload)
        if r.status_code != 200:
            # raise Exception('Could not get SMT result')
            pass
        else:
            return_data = json.loads(r.text)
            status = return_data['status']
            if status in ('error', 'done'):
                msg = '''
                task id: %s
                status code: %s
                return data: %s
                ''' %(task_id, r.status_code, return_data)
                logger.info(msg)
                task_link = return_data['task_link']
                smt_job_url = return_data['log']['build_url']
                if status == 'error':
                    is_success = False
                elif status == 'done':
                    is_success = True if int(return_data['log']['fail_count']) == 0 else False
                else:
                    raise SMTException('SMT return unknown status %s!' % status)
                break
            else:
                time.sleep(60)
    return is_success, smt_job_url, task_link


class SMTException(Exception): pass


class SMTNotConfigException(Exception): pass


class OamSMT(object):

    def __init__(self, job_name, build_num, build_url=None, gerrit_ref=None):
        self.job_name = job_name
        self.build_num = build_num
        if  build_url:
            self.build_url = build_url
        else:
            self.build_url = self._get_build_url()
        self.gerrit_ref = gerrit_ref

    def _get_build_url(self):
        return '%s/job/%s/%s' % (config.JENKIN_SERVER, self.job_name, self.build_num)

    def run_smt(self):
        url = config.SMT_CALL_API
        payload = {'project_name': self.job_name, 'build_num': self.build_num}
        taskid_list = []
        r = requests.get(url, params=payload)
        logger.debug('Call SMT url: %s' % r.url)
        if r.status_code != 200:
            raise Exception('Could not trigger SMT')
        else:
            return_data = json.loads(r.text)
            logger.debug('Call SMT return: %s' % return_data)
            status = return_data['status']
            if status == 'not_config':
                raise SMTNotConfigException('Call SMT failed. Reason is %s' % return_data['msg'])
            elif status != 'ok':
                raise SMTException('Call SMT failed. Reason is %s' % return_data['msg'])
            taskid_list = return_data['taskid']
        return taskid_list

    def _get_mail_body(self, smt_sucess, result_detail):
        smt_result = 'SUCCESS' if smt_sucess else 'FAIL'
        msg = ['SMT result is %s' % smt_result]
        msg.append('SMT case detail:')
        for is_success, smt_job_url, task_link in result_detail:
            if is_success:
                msg.append('<font color="green">SUCCESS: task link: %s smt job url: %s</font>' % (task_link, smt_job_url))
            else:
                msg.append('<font color="red">FAIL: task link: %s smt job url: %s</font>' % (task_link, smt_job_url))
        return '<br/>'.join(msg)

    def send_mail(self, smt_sucess, result_detail, err_msg = None):
        if err_msg:
            msg = 'Met a Problem when run SMT: %s' % err_msg
        else:
            msg = self._get_mail_body(smt_sucess, result_detail)
        logger.debug('Mail content is %s' % msg)
        oam_sender = OamMailSender(**{'job_name': self.job_name, 'build_url': self.build_url, 'phase': 'SMT', 'status': 'success' if smt_sucess else 'fail', 'msg': msg})
        oam_sender.send_mail()

    def call_smt_promotion(self, promotion_name='smt_done'):
        promotion_url = '%s/promotion/forcePromotion' % (self.build_url)
        payload = {'name': promotion_name}
        r = requests.get(promotion_url, params=payload, auth=(config.JENKINS_USER, config.JENKINS_PASSWORD))
        # logger.debug(r.text)
        if r.status_code != requests.codes.ok:
            logger.error('call smt promotion return non-ok code %d', r.status_code)
            r.raise_for_status()

    def run(self):
        try:
            taskid_list = self.run_smt()
            logger.debug('Get SMT taskids %s' % taskid_list)
            pool = Pool(3)
            results = pool.map(get_smt_result, taskid_list)
            final_result = True
            for is_success, smt_job_url, task_link in results:
                if not is_success:
                    final_result = False
                    break
            self.send_mail(final_result, results)
            if final_result and not self.gerrit_ref:
                self.call_smt_promotion()
        except SMTNotConfigException, sne:
            err_msg = str(sne)
            self.send_mail(True, [], err_msg)
            if not self.gerrit_ref:
                self.call_smt_promotion()
        except SMTException, se:
            err_msg = str(se)
            logger.error('Met a error during smt: %s.\nSend the mail.' % err_msg)
            self.send_mail(False, [], err_msg)
            raise
        except Exception:
            raise


def create_parser():
    parser = argparse.ArgumentParser(description='SMT resetapi caller', conflict_handler='resolve')
    parser.add_argument('-v', '--verbose', action='store_true', help='set debug mode')
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')

    parser_default = subparsers.add_parser('run_and_wait', help='call smt and wait')
    parser_default.add_argument('-j', '--job_name', help='job name to run smt')
    parser_default.add_argument('-b', '--build_num', help='jenkins job build number')
    parser_default.add_argument('-B', '--build_url', help='jenkins job build url')
    parser_default.add_argument('-g', '--gerrit_ref', help='gerrit ref which trigger this smt')

    return parser


def test():
    logger.setLevel(logging.DEBUG)
    oam_smt = OamSMT()
    oam_smt.build_url = 'http://hzacivm01.china.nsn-net.net:8080/view/oam/job/oam_trunk_cci_raktor-test-yongtzha/1/'
    oam_smt.call_smt_promotion()
    sys.exit()

if __name__ == '__main__':
    parser = create_parser()
    # args=parser.parse_args('run_and_wait -j  oam_trunk_cci_raktor -b 2801 '.split())
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.job_name or not args.build_num:
        logger.error('Job name or build number could not be empty!')
        parser.print_help()
        sys.exit(110)
    if args.action == 'run_and_wait':
        oam_smt = OamSMT(args.job_name, args.build_num, args.build_url, args.gerrit_ref)
        oam_smt.run()
    else:
        print 'unsupported arguments.'
        parser.print_help()
        sys.exit(110)

    sys.exit()
