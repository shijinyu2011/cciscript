"""
SvnInterface is a class which executes the subversion commandline client commands 
as subprocesses. All commands MUST be run with username and password and with --no-auth-cache. 
"""

import subprocess
import shlex

class SvnInterface(object):
    """
    Interface for using the commandline subversion client.
    """
    def __init__(self, username, password):
        """
        Constructor takes username and password as parameter.
        """
        self.username = username
        self.password = password
    
    def _execute(self, command):
        """
        Executes the command and returns stdout, stderr as tuple
        Raises SvnException if the the command was not executed succesfully.
        """
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()
        if process.returncode != 0:
            raise SvnException(process.returncode)
        
        return output
    
    def _execute_with_realtime_output(self, command):
        """
        Executes the command and prints the output in realtime. After the command
        has been executed, returns the output.
        """
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = p.stdout.readline()
            print line.strip('\n')
            if not line:
                break
        out, err = p.communicate()
        if p.returncode != 0:
            raise SvnException(p.returncode)

    def get_externals(self, url):
        """
        Returns svn:externals -property from given URL
        """
        command = 'svn pg svn:externals --username %s --password %s --no-auth-cache %s --trust-server-cert --non-interactive' % (self.username, self.password, url)
        return self._execute(command)
    
    def list(self, url):
        """
        Returns svn list from given url
        """
        command = 'svn ls --username %s --password %s --no-auth-cache %s --trust-server-cert --non-interactive' % (self.username, self.password, url)
        return self._execute(command)
    
    def switch(self, url, subsystem_name, realtime_output=False):
        """
        Runs svn switch for folder given as subsystem_name.
        Switches to repository given as url.
        Returns stdout and stderr as tuple.
        """
        command = 'svn switch --username %s --password %s --no-auth-cache %s %s --trust-server-cert --non-interactive' % (self.username, self.password, url, subsystem_name)
        if realtime_output:
            self._execute_with_realtime_output(command)
        else:
            return self._execute(command)
        return self._execute(command)
    
    def checkout(self, url, target_folder, realtime_output=False):
        """
        Runs svn checkout command to target url.
        Stores the data to target_folder
        Returns stdout and stderr as tuple
        """
        command = 'svn checkout --username %s --password %s --no-auth-cache %s %s --trust-server-cert --non-interactive' % (self.username, self.password, url, target_folder)
        if realtime_output:
            self._execute_with_realtime_output(command)
        else:
            return self._execute(command)

    def info(self, url):
        """
        Returns svn list from given url
        """
        command = 'svn info --username %s --password %s --no-auth-cache %s --trust-server-cert --non-interactive' % (self.username, self.password, url)
        return self._execute(command)

    def get_property(self, url, property):
        command = 'svn pg %s --username %s --password %s --no-auth-cache %s --trust-server-cert --non-interactive' % (property, self.username, self.password, url)
        return self._execute(command)

    def cat(self, url):
        command = 'svn cat --username %s --password %s --no-auth-cache %s --trust-server-cert --non-interactive' % (self.username, self.password, url)
        return self._execute(command)

    def local_info(self, path):
        command = 'svn info %s' % path
        return self._execute(command)

class SvnException(Exception):
    def __init__(self, value):
        self.parameter = value
    
    def __str__(self):
        return repr(self.parameter)
    

