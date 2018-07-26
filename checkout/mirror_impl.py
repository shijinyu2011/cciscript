"""
Interface for using command-line SVN -client from python. Creates a 
subprocess from every SVN -command. 
"""

import re
import os
import sys
import subprocess

class SVN(object):
    def __init__(self, username, password, src_url, dst_url):
        self.username = username
        self.password = password
        self.src_url = src_url
        self.dst_url = dst_url
        m = re.match('file://(.*)', self.dst_url)
        if m is None:
            raise Exception('Mirror must have "file://" URI')
        else:
            self.dst_path = m.group(1)
    
    def __execute(self, command):
        """
        Executes the command and returns the output
        """
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = process.communicate()[0]
        
        return output
        
    def __executeWithRealTimeOutput(self,command):
        """
        Executes the command and prints the output in realtime. After the command
        has been executed, returns the output.
        """
      	p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = p.stdout.readline()
            print line.strip('\n')
            if not line:
                break
        
    
    def _mirror_url(self, url):
        """
        Get local mirror url if the local mirror exists. Otherwise return None
        """
        m = re.match(self.src_url + '(.*)', url)
        if m is not None:
            new_url = self.dst_url + m.group(1)
            m = re.match('file://(' + self.dst_path + '/[^/]*)/.*', new_url)
            if m is not None and os.path.exists(m.group(1)):
                print "Using mirror: %s" % (new_url)
                return new_url
        else:
            print "Won't search for mirror because %s is not from %s" % (url, self.src_url)
        return None

    def _is_from_mirror(self, local_path):
        """
        Return True if local path is checked out from mirror repository
        """
        command = ['svn', 'info', local_path]
        output = self.__execute(command)
        mirror = False
        for line in output.split('\n'):
            m = re.search(self.dst_url, line)
            if m is not None:
                print "%s is from mirror" % (local_path)
                return True
        print "%s is not from mirror" % (local_path)
        return False

    def checkout(self, url, targetfolder):
        """
        Does svn checkout from local mirror if exists. Otherwise delegates to parent
        """
        mirror_url = self._mirror_url(url)
        if mirror_url is not None:
            command = ['svn', 'checkout', mirror_url, targetfolder]        
        else:
            command = ['svn', 'checkout', '--username', self.username, '--password', self.password, '--no-auth-cache', url, targetfolder]        
        return self.__executeWithRealTimeOutput(command)
    
    def switch(self, url, subsystemName):
        if self._is_from_mirror(subsystemName):
            mirror_url = self._mirror_url(url)
            command = ['svn', 'switch', mirror_url, subsystemName]
        else:
            command = ['svn', 'switch', '--username', self.username, '--password', self.password, '--no-auth-cache', url, subsystemName]
        return self.__executeWithRealTimeOutput(command)
    
    def update(self, targetFolder):
        if self._is_from_mirror(targetFolder):
            command = ['svn', 'update', targetFolder]      
        else:
            command = ['svn', 'update', '--username', self.username, '--password', self.password, '--no-auth-cache', targetFolder]
        return self.__executeWithRealTimeOutput(command)
    
    def get_externals(self, url):
        """
        Gets svn:externals from url and returns them in dictionary 
        where key is subsystem name and value is url to subsystem
        """
        mirror_url = self._mirror_url(url)
        if mirror_url is not None:
            command = ['svn', 'pg', 'svn:externals', mirror_url]
        else:
            command = ['svn', 'pg', 'svn:externals', '--username', self.username, '--password', self.password, '--no-auth-cache', url]
    
        return self.__execute(command)
            
    def list(self, url):
        mirror_url = self._mirror_url(url)
        if mirror_url is not None:
            command = ['svn', 'ls', mirror_url]
        else:
            command = ['svn', 'ls', '--username', self.username, '--password', self.password, '--no-auth-cache', url]
        return self.__execute(command)
    
    def get_all_dependencies(self, url):
        """
        Gets the dependencies from url specified
        under specified rislabel. Returns the information in dict where key is 
        subsystem name and value is list of its dependencies  
        """
        mirror_url = self._mirror_url(url)
        if mirror_url is not None:
            command = ['svn', 'pg', mirror_url]
        else:
            command = ['svn', 'pg', 'svntask:ssdeps', '--username', self.username, '--password', self.password, '--no-auth-cache', url]
        return self.__execute(command)
          
