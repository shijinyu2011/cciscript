import os
import json
import logging
import argparse
import sys
import requests
import os.path
from requests.auth import HTTPDigestAuth,HTTPBasicAuth

FORMAT = "++%(asctime)s--%(filename)-10s--%(lineno)-3s:\n %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
logger=logging.getLogger(__name__)

gerrit_servers={
    "gerrit.nsn-net.net":('http://gerrit.nsn-net.net','hzci','RoaD+HsmJZQ/'),
    'gerrite1.ext.net.nokia.com':('https://gerrite1.ext.net.nokia.com','hzci','b2a6eefb'),
    # 'gerrite1.ext.net.nokia.com':('https://gerrite1.ext.net.nokia.com','hzci','b2a6eefb')
}

headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'base': ''}

if 'GERRIT_SERVER' in os.environ:
    GERRIT_SERVER = os.environ.get('GERRIT_SERVER')
else:
    GERRIT_SERVER='gerrit.nsn-net.net'

class GerritRebaseException(Exception):pass

class GerritServer(object):

    def __init__(self,url=GERRIT_SERVER):
        if url.endswith("/"):
            gerrit_url=url[:-1]
        else:
            gerrit_url=url
        self.url, self.username, self.password=gerrit_servers[gerrit_url]
        logger.debug('url: %s' %self.url)
        logger.debug('user: %s' %self.username)

    def get_change_filed(self,change,field,revision_id='current'):
        query_url='%s/changes/%s?o=CURRENT_REVISION&o=LABELS' %(self.url,change)
        logger.debug('query url is %s' %query_url)
        resp=requests.get(query_url)
        if resp.status_code == 200:
            change_data=json.loads(resp.text[4:])
            logger.debug('change-%s:\n%s' %(change,change_data))
            if change_data:
                if field == 'fetch_ref':
                    cur_rev = change_data['current_revision']
                    try:
                        return change_data['revisions'][cur_rev]['ref']
                    except KeyError:
                        return change_data['revisions'][cur_rev]['fetch']['anonymous http']['ref']
                elif field == 'verified_flag':
                    return 'approved' in change_data['labels']['Verified']
                elif field == 'review_flag':
                    return 'approved' in change_data['labels']['Code-Review']
                elif field == 'patch_number':
                    cur_rev = change_data['current_revision']
                    return change_data['revisions'][cur_rev]['_number']
                elif field in change_data:
                    return change_data[field]
        else:
            logger.error('Meet a problem when get change %s field %s, status code: %s error info: %s' %(change,field,resp.status_code,resp.text))
            return 


    def get_resp_with_auth(self,url,data):
        '''for POST method only'''
        # auth_calsses=[HTTPBasicAuth,HTTPDigestAuth]
        # for auth_class in auth_calsses:
        logger.debug("post url: %s"%url)
        logger.debug("headers: %s"%headers)
        logger.debug("username: %s  password:%s "%(self.username,self.password))
        logger.debug(json.dumps(data))
        cmd="curl  -u  %s:%s -H \"Content-Type: application/json\" -X POST --data '%s' %s"%(self.username,
            self.password,json.dumps(data),url)
        logger.debug("excute: %s"%cmd)
        resp=os.system(cmd)
            # resp=requests.post(url,data=json.dumps(data),auth=auth_class(self.username,self.password),headers=headers)
            # resp.raise_for_status()
            # if resp.status_code == 401:
            #     continue
            # else:
            #     break
        return resp

    def submit(self,change_id):
        data = {'wait_for_merge': True }
        url = "%s/a/changes/%s/submit" %(self.url,change_id)
        resp=self.get_resp_with_auth(url,data)
        if resp.status_code == 200:
            return True
        else:
            logger.error('Meet a problem when review change %s, status code: %s error info: %s' %(change_id,resp.status_code,resp.text))
            return False

    def review(self,change_id,revision_id='current',code_review=None,verified=None,message=None):
        if not code_review and not verified and not message:
            print 'At least one of code_review or verified or message is needed!'
            return False
        logger.info('start review change %s' %change_id)
        url='%s/a/changes/%s/revisions/%s/review' %(self.url,change_id,revision_id)
        data={'labels':{}}
        if code_review and code_review in ('+2','+1','0','-1','-2'):
            data['labels']['Code-Review']=code_review
        if verified and verified in ('+1','0','-1'):
            data['labels']['Verified']=verified
        if message:
            data['message']=message
        resp=self.get_resp_with_auth(url,data)
        # if resp.status_code == 200:
        #     return True
        if resp==0:
            return True
        else:
            print 'Meet a problem when review change %s, status code: %s error info: %s' %(change_id,resp.status_code,resp.text)
            return False

    def rebase(self,change_id):
        print 'start rebase change %s' %change_id
        data={'base': ' '}
        url="%s/a/changes/%s/rebase" %(self.url,change_id)
        resp=self.get_resp_with_auth(url,data)
        logger.info('rebase return: %s'%resp.text)
        if resp.status_code == 200:
            return True
        elif 'Change is already up to date' in resp.text or 'change is merged' in resp.text:
            return True
        else:
            logger.error('Meet a problem when rebase change %s, status code: %s error info: %s' %(change_id,resp.status_code,resp.text))
            return False

    def rebase_and_compare(self,change_id):
        org_patch_num=self.get_change_filed(change_id,'patch_number')
        if self.rebase(change_id):
            new_patch_num=self.get_change_filed(change_id,'patch_number')
            if new_patch_num != org_patch_num:
                logger.info('rebase create a new patchset!')
                raise GerritRebaseException('rebase create a new patchset!')
        else:
            raise GerritRebaseException('rebase failed!')

def create_parser():
    parser=argparse.ArgumentParser(description='Gerrit Info Query and Action',epilog='you could export GERRIT_SERVER or use default  http://gerrit.nsn-net.net/',conflict_handler='resolve')
    parser.add_argument('-v','--verbose',action='store_true',help='set debug mode')
    subparsers=parser.add_subparsers(help='sub-command help',dest='action')

    parser_query=subparsers.add_parser('query',help='query change info')
    parser_query.add_argument('-c','--change',help='gerrit change id')
    parser_query.add_argument('-f','--field',help='the gerrit change field to query')

    parser_submit=subparsers.add_parser('submit',help='submit change')
    parser_submit.add_argument('-c','--change',help='gerrit change id')

    parser_rebase=subparsers.add_parser('rebase',help='rebase change')
    parser_rebase.add_argument('-c','--change',help='gerrit change id')    

    parser_rebase=subparsers.add_parser('rebase_and_compare',help='rebase change and check if new patchset is created')
    parser_rebase.add_argument('-c','--change',help='gerrit change id')

    parser_review=subparsers.add_parser('review',help='review change')
    parser_review.add_argument('-c','--change',help='gerrit change id')
    parser_review.add_argument('-r','--code_review',choices=('+2','+1','0','-1','-2'))
    parser_review.add_argument('-v','--verified',choices=('+1','0','-1'))
    parser_review.add_argument('-m','--message',help='review message')

    return parser

if __name__ == '__main__':
    parser=create_parser()
    # args=parser.parse_args('--verbose query -c 27889 -f project'.split())
    args=parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    gs=GerritServer()
    # gs=GerritServer('gerrite1.ext.net.nokia.com')
    if args.action == 'query':
        if args.change and args.field:
            print gs.get_change_filed(args.change,args.field)
        else:
            parser.print_usage()
            sys.exit(110)
    elif args.action == 'rebase' and args.change:
        if not gs.rebase(args.change):
            sys.exit(110)
    elif args.action == 'rebase_and_compare' and args.change:
        gs.rebase_and_compare(args.change) 
    elif args.action == 'submit' and args.change:
        if not gs.submit(args.change):
            sys.exit(110)
    elif args.action == 'review' and args.change:
        if args.verified or args.code_review or args.message:
            if not gs.review(args.change,'current',args.code_review,args.verified,args.message):
                sys.exit(110)
    else:
        print 'unsupported arguments.'
        parser.print_help()
        sys.exit(110)

    sys.exit()