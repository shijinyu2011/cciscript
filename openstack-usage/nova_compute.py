import os
import sys
import subprocess
import shlex
import re
import yaml
import datetime
from os import environ as env
from multiprocessing import Process, Queue
from copy import deepcopy
import paramiko
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException
from paramiko.client import SSHClient
from novaclient.client import Client as NovaClient

class SshconnectionProcess(object):
    def __init__(self, host):
        self.host = host
        self.queue = Queue()

    def get_instance_connections(self, host, port=22, username='_rcpadmin', password='RCP_owner'):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(host, 22, username, password, timeout=60)
        stdin, stdout, stderr = client.exec_command('date +"%Y-%m-%d %H:%M"')
        now = datetime.datetime.strptime(stdout.read().strip(), '%Y-%m-%d %H:%M')
        stdin, stdout, stderr = client.exec_command('who -u')
        result = stdout.read().strip().splitlines()
        before_30min = now - datetime.timedelta(minutes=30)
        f = lambda x: re.search('\.|00:[0-2]\d', x.split()[-3]) or \
                                datetime.datetime.strptime(str(now.year) + ' '+ ' '.join(x.split()[2:5]), '%Y %b %d %H:%M')>=before_30min
        result = filter(f, result)
        client.close()
        return result

    def get_connections(self, host):
        ttys = []
        try:
            ttys = self.get_instance_connections(host)
        except AuthenticationException, msg:
            try:
                ttys = self.get_instance_connections(host=host, username='root', password='rootme')
            except Exception, emsg:
                print '*WARN*', "ssh connection error: ", host, emsg                    
        except BadHostKeyException, badhostmsg:
            print '*WARN*', "ssh connection error: BadHostKeyException, ", host, badhostmsg
        except Exception, exmsg:
            print '*WARN*', 'unknown exception, ', host, exmsg
        finally:
            self.queue.put(ttys)

    def run(self):            
        p = Process(target=self.get_connections, args=(self.host, ))
        p.start()
        p.join(60)
        if p.is_alive():
            p.terminate()

    def return_result(self):
        return self.queue.get()

class NovaComputeClient(object):
    def __init__(self):
        self.credentials = self._get_nova_credentials_v2()

    def _get_nova_credentials_v2(self,):
        d = {}
        d['version'] = '2'
        d['username'] = env['OS_USERNAME']
        d['api_key'] = env['OS_PASSWORD']
        d['auth_url'] = env['OS_AUTH_URL']
        d['project_id'] = env['OS_TENANT_NAME']
        return d

    def nova_auth(self,):        
        nova_client = NovaClient(**self.credentials)
        return nova_client
    
    def nova_usage(self, nova_client, start, end):
        start = datetime.datetime.strptime(start,'%Y-%m-%d') #'2015-04-20' 
        end = datetime.datetime.strptime(end,'%Y-%m-%d')  # '2015-04-20'
        project_usages = nova_client.usage.list(start=start, end=end)
        keypairs = nova_client.keypairs.list()
        servers = nova_client.servers.list()
        # {u'OMS_net': [u'190.254.2.4'], u'management_net': [u'192.168.1.103', u'10.70.40.212'], 
        # u'access_net': [u'200.254.2.2'], u'internal_net': [u'169.254.0.4']}
        print servers[0].id, servers[0].networks

class OpenstackStatistics(object):
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.project_list = []
        self.floating_ips = {}
        self.report_result = []

    def keystone_project_list(self):
        '''
        command: openstack project list, keystone tenant-list(deprecated)
        '''
        def _keystone_auth():            
            import keystoneclient.v2_0.client as ksclient
            client = ksclient.Client(auth_url=env['OS_AUTH_URL'],
                                       username=env['OS_USERNAME'],
                                       password=env['OS_PASSWORD'],
                                       tenant_name=env['OS_TENANT_NAME'],
                                       region_name=env['OS_REGION_NAME'])
            return client
    
        client = _keystone_auth()
        self.project_list = client.tenants.list()

    def neutront_floating_ip_list(self, ):
        '''
        command: neutron floatingip-list
        '''
        def _neutront_auth():
            from neutronclient.v2_0 import client as neutronclient
            client = neutronclient.Client(auth_url=env['OS_AUTH_URL'],
                                       username=env['OS_USERNAME'],
                                       password=env['OS_PASSWORD'],
                                       tenant_name=env['OS_TENANT_NAME'])
            return client

        client = _neutront_auth()
        netfloatingips = client.list_floatingips()
        for ip in netfloatingips['floatingips']:
            self.floating_ips.setdefault(ip['tenant_id'], []).append(ip)    
    
    def run(self):
        self.keystone_project_list()
        self.neutront_floating_ip_list()
        self.report()

    def report(self):
        '''
        Get instance and connection info for all enabled projects.
        '''
        for project in self.project_list:
            if not project.enabled:
                continue
            ttys = []
            p = subprocess.Popen('nova list --tenant %s'%project.id, shell=True, stdout=subprocess.PIPE)
            output = p.stdout.read()
            serverlist = filter(lambda x: x.count(project.id), output.splitlines()).__len__()  
            floatingIP = self.floating_ips.get(project.id, [])
            floatingips = [ip.get('floating_ip_address').encode('ascii') for ip in floatingIP if ip.get('status')=='ACTIVE']
            print "====INFO====", project.name, project.enabled, project.id, serverlist, floatingips
            if not project.enabled:
                continue            
            ttys = []
            for ip in floatingips:
                if not self.ping_ip_reachable(ip):
                    continue
                sshp = SshconnectionProcess(ip)
                sshp.run()
                ttys += sshp.return_result()
            self.report_result.append({project.name.encode('ascii'): \
                                    {'instance':serverlist, 'connection':ttys.__len__(), 'enable': project.enabled, \
                                     'tenant_id':project.id.encode('ascii'), 'floatingips':floatingips}})
    def ping_ip_reachable(self, host):
        cmd=shlex.split("ping -c1 %s"%host)
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError, e:
            return False
        else:
            return True

    def report_yaml(self):        
        if not os.path.exists('projects_usage_rate.records'):
            f = open('projects_usage_rate.records', 'w')
            f.close()
        with open('projects_usage_rate.records', 'r') as fr:
            yaml_data = yaml.load(fr.read()) or []  
            with open('projects_usage_rate.records', 'w') as fw:
                yaml_data.append({'date':self.timestamp, \
                                  'host':re.search('http://(\d+.\d+.\d+.\d+):', env['OS_AUTH_URL']).group(1), \
                                  'projects': self.report_result})
                fw.write(yaml.dump(yaml_data[-500:]))
            
    def report_db(self):
        '''
        table: projects_usage
        fields:
          - name: varchar(32), project name, 
          - host: varchar(16), openstack host ip
          - instance: int(4), project instances
          - connection: int(4), instance connections
          - date: varchar(20), sample timestamp
        '''
        import sqlite3
        host = re.search('http://(\d+.\d+.\d+.\d+):', env['OS_AUTH_URL']).group(1)
        cx = sqlite3.connect("projects_usage.db")
        cu = cx.cursor()
        cu.execute("""create table IF NOT EXISTS projects_usage \
                    (name varchar(32), host varchar(16), instance int(4), \
                    connection int(4), date varchar(20), active varchar(1), \
                    floatingips varchar(96), primary key (name,date))""")
        
        for p in self.report_result:
            k = p.keys()[0]
            v = p.values()[0]           
            cu.execute("insert into projects_usage (name, host, instance, connection, date, active, floatingips) values \
                    ('%s', '%s', %d, %d, '%s', '%s', '%s')"%(k, host, v['instance'], v['connection'], \
                                                       self.timestamp, v['enable'] and 'Y' or 'N', ";".join(v['floatingips'])))
        cx.commit()
        cu.close()
        cx.close()

class OpenstackStatisticsSsh(OpenstackStatistics):
    '''
    Gets all info by connecting to openstack controller through ssh 
    '''

    def __init__(self):
        super(OpenstackStatisticsSsh, self).__init__()

    def keystone_project_list(self):
        '''
        command: openstack project list, keystone tenant-list(deprecated)
        '''
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(env['OS_SSH_HOST'], username=env['OS_SSH_USERNAME'], password=env['OS_SSH_PASSWORD'])
        stdin, stdout, stderr = client.exec_command('source /etc/nova/openrc && openstack project list --long')
        output = stdout.read()
        self.project_list = re.findall('(\w{32})\s+\|\s+([\w-]+)\s+\|\s+[\w\t]*\s+\|\s+(True|False)\s+\|', output)
        client.close()
 
    def neutront_floating_ip_list(self):
        '''
        command: neutron floatingip-list [--show-details], neutron floatingip-show FLOATINGIP_ID
        '''
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(env['OS_SSH_HOST'], username=env['OS_SSH_USERNAME'], password=env['OS_SSH_PASSWORD'])
        stdin, stdout, stderr = client.exec_command('source /etc/nova/openrc && neutron floatingip-list')
        output = stdout.read()
        self.floating_ips = re.findall('([\w-]+)\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|\s+([\w-]+)', output)
        client.close()
    
    def report(self):
        '''
        Get instance and connection info for all enabled projects.
        '''
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(env['OS_SSH_HOST'], username=env['OS_SSH_USERNAME'], password=env['OS_SSH_PASSWORD'])
        for project in self.project_list:
            if not eval(project[2]) or project[1] in ('admin', 'services'):
                continue
            ttys = []
            stdin, stdout, stderr = client.exec_command('source /etc/nova/openrc && nova list --tenant %s'%project[0])            
            output = stdout.read()
            serverlist = filter(lambda x: x.count(project[0]), output.splitlines()).__len__() 
            stdin, stdout, stderr = client.exec_command('source /etc/nova/openrc && neutron floatingip-list --tenant-id %s -F floating_ip_address'%project[0])
            floatingips = re.findall('\d+\.\d+\.\d+\.\d+', stdout.read())
            print "====INFO====", project[1], project[2], project[0], serverlist, floatingips
            ttys = []
            for ip in floatingips:
                if not self.ping_ip_reachable(ip):
                    continue
                sshp = SshconnectionProcess(ip)
                sshp.run()
                ttys += sshp.return_result()
            self.report_result.append({project[1].encode('ascii'): \
                                    {'instance':serverlist, 'connection':ttys.__len__(), 'enable': eval(project[2]), \
                                     'tenant_id':project[0].encode('ascii'), 'floatingips':floatingips}})
        client.close()

def main():
    c = (sys.argv[1] == 'SSH') and  OpenstackStatisticsSsh or OpenstackStatistics
    o = c()
    o.run()
    o.report_yaml()
    o.report_db()
    
if __name__ == '__main__':
    main()
