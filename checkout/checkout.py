import subprocess
import sys
import os
import re

from optparse import OptionParser
from ConfigParser import RawConfigParser

CWLC_CCI_SUBSYSTEM_LIST = [
    "RCPNetworkManager",
    "SS_DPDK",
    "SS_HAProxy",
    "SS_MOMfsSGW",
    "SS_PSRELENV",
    "SS_SGWLibNMLM",
    "SS_SGWLM",
    "SS_SGWNM",
    "SS_SGWSCLI",
    "SS_SGWStacks",
    "SS_TestRCPHAProxy",
    "SS_TestRCPIPSecMgmt",
    "SS_TestRCPCCSRT",
    "SS_TestRCPCCSMCU",
    "SS_TestRCPNTP",
    "SS_TestRCPCLM",
    "SS_TestRCPHA",
    "SS_ZMQLib",
    "SS_SignalingFPCM",
    "rcppmuploader",
    "rcppmuploadercmapi",
    "rcploglib",
    "SS_DDRCPProduct",
    "SS_DDRCPRefCnfs",
    "SS_DDRCPTypes",
]
VRNC_CCI_SUBSYSTEM_LIST = []
IRREGULARITY_I_NAME = {
"ss_rcpnetsnmp":"i_netsnmp",
"ss_rcpaaa":"i_aaa",
"ss_psrelenv":"i_interface",
"ss_rcpipsecmgmt":"i_ipsecmgmt",
}

SUBSYSTEM_GIT_LIST = []
SUBSYSTEM_GIT_LIST.extend([x.lower() for x in CWLC_CCI_SUBSYSTEM_LIST])
SUBSYSTEM_GIT_LIST.extend([x.lower() for x in VRNC_CCI_SUBSYSTEM_LIST])

parser = OptionParser()
parser.add_option("-s", "--subsystem",
                  action="store",
                  dest="ss_names",
                  help="Comma separated list of subsystems to checkout (case sensitive)")
                  
parser.add_option("-d", "--to-dir",
                  action="store",
                  dest="directory",
                  help="Optional. Relative or absolute path to directory to checkout into. Will be created if it does not exists. Defaults to '.'")

parser.add_option("-p", "--product",
                  action="store",
                  dest="product",
                  help="Optional. The name of the product, e.g. IL, MCRNC, ADA. This will be used to find out the correct SVN URL, folders that are always checked out etc. Default is IL.")

parser.add_option("-r", "--root",
                  action="store",
                  dest="svn_root",
                  help="Optional. The ROOT SVN url. Different defaults for different products. E.g. https://svne1.access.nsn.com")

parser.add_option("-t", "--trunk",
                  action="store",
                  dest="svn_trunk",
                  help="Optional. SVN trunk (or branch) folder. Different defaults for different products. E.g. isource/svnroot/scm_il/trunk/ipal-main-beta")

parser.add_option("-b", "--branch",
                  action="store",
                  dest="branch_name",
                  help="Optional. Branch, if used. This should be found as its own section in conf/<product_name>.cfg. Defaults to 'TRUNK'")
parser.add_option("-g", "--git-https",
                  action="store_true",
                  dest="git_https",
                  help="Use HTTPS over SSH when cloning and checking out projects from GIT. Use this if SSH is unavailable.")
parser.add_option("--ef", "--externals-file",
                  dest="externals_file",
                  default="default",
                  help="Use a file for externals, instead of svn:externals.")
parser.add_option("--gf","--git-repo-file",
                  dest="git_file",
                  default="default",
                  help="Get gitrepo.lst from a file instead of the repository.")
parser.add_option("--deps",
                  dest="deps_file",
                  default="default",
                  help="Get dependencies from a file instead of the repository.")
parser.add_option("-f", "--gerrit-refspec",
                  action="store",
                  dest="gerrit_refspec",
                  help="Optional.Gerrit refspec for running gerrit triggered cci")
parser.add_option("--ft", "--freezed_tag",
                  action="store",
                  dest="tag_name",
                  help="Optional. Build level tag, if used. This should be found as its own section in conf/<product_name>.cfg. Defaults to 'TRUNK'")


def format_product(product, branch):
    products = ["vrnc", "vbgw", "mcrnc", "rcp"]

    if product in products:
        config = RawConfigParser()
        config.read('%s/conf/%s.cfg' %(sys.path[0], product))

        try:
            SVNROOT = config.get('COMMON_VALUES', 'SVNROOT')
            SVNTRUNK = config.get(branch, 'SVNTRUNK')
            SUBSYSTEMS = config.get(branch, 'SUBSYSTEMS')
            SUBSYSTEMS = SUBSYSTEMS.split()
        except:
            print "\nERROR while reading values from section [%s] in conf/%s.cfg!\n" %(branch, product)
            sys.exit(1)
    else:
        print "ERROR: product (%s) not found! Exiting." %product
        print "All products: %s" %products
        sys.exit(1)

    return SVNTRUNK, SVNROOT, SUBSYSTEMS

def execute(args, working_directory=None):
    try:
        if working_directory == None:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
    except RuntimeError:
        print("Failed to execute command: " + args)
    output, errors = p.communicate()
    return output, errors

def fetch_property_value(url, property):
   return execute(["svn", "propget", property, url])[0]

def svn_checkout(url, target):
    return execute(["svn", "checkout", url, target])[0]
    
def gerrit_checkout(command, target):
    return execute([command, target])

def svn_list_branch(url):
   return execute(["svn", "ls", url])[0]   

def git_checkout(url, branch, target, https=False):
    try:
        if https==True:
            if not url.startswith('ssh'):
                url = url.replace(':', '/')
            url = url.replace('git@', 'https://')
            clone_output, clone_errors = execute(["git", "clone", "-c http.sslVerify=false", "-n", url, target])
        else:
            clone_output, clone_errors = execute(["git", "clone", "-n", url, target])
    except RuntimeError:
        print("Failed cloning " + target + " from " + url)
    clone_errors = clone_errors.strip().split('\n')
    errors = []
    for line in clone_errors:
        if not line.startswith("Cloning into"):
            errors.append(line)
    if len(errors) == 0:
        working_directory = os.path.join(os.getcwd(),target)
        try:
            if branch != "master":
                checkout_output, checkout_errors = execute(["git", "checkout", branch], working_directory)
            else:
                checkout_output, checkout_errors = execute(["git", "checkout"], working_directory)
                checkout_output = checkout_output.strip()
        except RuntimeError:
            print("Failed to checkout branch " + branch + " for " + target)
        if checkout_output != "":
            return ("", checkout_errors.strip())
    else:
        checkout_output = ""
        return (errors, "")
    return ("","")
    
def fetch_and_parse_gitrepos(url, repo_file):
    fetch_output, errors = execute(["svn", "export", "--force", url+repo_file])
    if errors != "":
        print "Error while fetching " + repo_file + ": " + errors
    output = ""
    with open(repo_file, "r") as gitrepo_lst:
        for line in gitrepo_lst.readlines():
            if not line.split() or line.startswith('#'):
                continue
            name = line.strip().split()
            name = re.search(r'([^:\/]+)$', name[0]).group(0)
            if name.endswith('.git'):
                name = name[:-4]
            output += line.strip() + " " + name + "\n"
    return output   
  
def fetch_externals(PRODUCT, dependency_graph, TRUNK, options, git=False):
    raw = ""
    rcpraw = ""
    newraw = ""
    if options.externals_file == "default":
        raw =  fetch_property_value(TRUNK, "svn:externals")
        #print "inside options.externals_file=default TRUNK=%s" %(TRUNK)
    else:
        with open(options.externals_file, "r") as externals_file:
            for line in externals_file:
                raw += line
    if PRODUCT == 'vrnc':
        for line in map(lambda x: x.strip(), raw.split("\n")):
            name = ''
            if line == '':
                continue
            elif line.startswith('#'):
                continue
            elif line.startswith('-r '):
                rev_option, rev_number, location, name = line.split()
            elif line.startswith('-r'):
                rev, location, name = line.split()
            elif line.split()[1].startswith('-r'):
                name, rev, location = line.split()
            elif not line.startswith('/'):
                name, rev, location = line.split()
            else:
                location, name = line.split()
            if name.endswith('_DPDK') or name == 'gbuild' or name =='flexiserver' or name =='fvntools' or name =='build' or name =='SS_ILThirdpart':
                continue
            else:
                newraw += line + "\n"
        rcpraw = fetch_property_value(TRUNK, "rcpsvn:externals")
        raw = newraw
        gitrepofile = 'gitrepo.rcp'
    else:
        gitrepofile = 'gitrepo.lst'

    if git == True:
        if options.git_file == "default":
            raw += fetch_and_parse_gitrepos(TRUNK, gitrepofile)
        else:
            with open(options.git_file, "r") as gitrepo_lst:
                for line in gitrepo_lst.readlines():
                    name = line.strip().split()
                    name = re.search(r'([^:\/]+)$', name[0]).group(0)
                    if name.endswith('.git'):
                        name = name[:-4]
                    raw += line.strip() + " " + name + "\n"
    svn_externals = dict()
    git_externals = dict()
    for line in map(lambda x: x.strip(), raw.split("\n")):
        if line == '':
            continue
        elif line.startswith('#'):
            continue
        if line.startswith('-r '):
            rev_option, rev_number, location, name = line.split()
            if PRODUCT == 'vrnc' and (name.endswith('_DPDK') or name == 'gbuild' or name =='flexiserver' or name =='fvntools' or name =='build' or name =='SS_ILThirdpart'):
                continue
            else:
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev_number)
        elif line.startswith('-r'):
            rev, location, name = line.split()
            if PRODUCT == 'vrnc' and (name.endswith('_DPDK') or name == 'gbuild' or name =='flexiserver' or name =='fvntools' or name =='build' or name =='SS_ILThirdpart'):
                continue
            else:
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev.replace('-r',''))
        elif line.startswith('git@') or line.startswith('ssh://git@'):
            location, branch, name = line.split()
            git_externals[name.lower()] = '%s %s' % (location, branch)
        elif not line.startswith('/'):
            name, rev, location = line.split()
            if PRODUCT == 'vrnc' and (name.endswith('_DPDK') or name == 'gbuild' or name =='flexiserver' or name =='fvntools' or name =='build' or name =='SS_ILThirdpart'):
                continue
            else:
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev.replace('-r',''))
        else:
            location, name = line.split()
            if PRODUCT == 'vrnc' and (name.endswith('_DPDK') or name == 'gbuild' or name =='flexiserver' or name =='fvntools' or name =='build' or name =='SS_ILThirdpart'):
                continue
            else:
                svn_externals[name.lower()] = '%s %s' % (name, location)
        if not dependency_graph.has_key(name.lower()):
            dependency_graph[name.lower()] = set()

    ## for cloud IL vrnc rcp common part
    if PRODUCT == 'vrnc':
        location = '/isource/svnroot/scm_il/branches/rcptrunk/tools'
        toolsname = 'tools'
        svn_externals[toolsname] = "%s %s" % (toolsname, location)
        if not dependency_graph.has_key(toolsname):
            dependency_graph[toolsname] = set()
        for line in map(lambda x: x.strip(), rcpraw.split("\n")):
            if line == '':
                continue
            elif line.startswith('#'):
                continue
            if line.startswith('-r '):
                rev_option, rev_number, location, name = line.split()
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev_number)
            elif line.startswith('-r'):
                rev, location, name = line.split()
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev.replace('-r',''))
            elif not line.startswith('/'):
                name, rev, location = line.split()
                svn_externals[name.lower()] = '%s %s@%s' % (name, location, rev.replace('-r',''))
            else:
                #print "inside without -r and not git. line=%s" %(line)
                location, name = line.split()
                svn_externals[name.lower()] = '%s %s' % (name, location)
            if not dependency_graph.has_key(name.lower()):
                dependency_graph[name.lower()] = set()
    return svn_externals, git_externals


def fetch_dependency_graph(PRODUCT, TRUNK, options):
    raw = ""
    if options.deps_file == "default":
        if PRODUCT == 'vrnc':
            raw = fetch_property_value(TRUNK, "rcpsvntask:ssdeps")
            raw += fetch_property_value(TRUNK, "vrncsvntask:ssdeps")
        else:
            raw = fetch_property_value(TRUNK, "svntask:ssdeps")
    else:
        with open(options.deps_file, "r") as deps_file:
            for line in deps_file:
                raw += line
    dependencies = dict()

    for line in map(lambda x: x.strip(), raw.split("\n")):
        if line == '':
            continue
        elif line.startswith('#'):
            continue
        ss, ss_deps = line.lower().split(":")

        dependencies[ss.lower()] = set()
        for kid in ss_deps.split():
            if kid == '' or kid == ss:
                continue
            dependencies[ss].add(kid)
    return dependencies
  

def resolve_dependencies(ss_name, dependency_graph, already_resolved = None):
    if already_resolved is None:
        already_resolved = set()
        
    dependencies = set()
    dependencies.add(ss_name.lower())
    
    already_resolved.add(ss_name.lower())
    
    if dependency_graph.has_key(ss_name.lower()):
        for kid in dependency_graph[ss_name.lower()]:
            if kid in already_resolved:
                continue
        
            dependencies |= resolve_dependencies(kid, dependency_graph, already_resolved)
        
    return dependencies

def export_gerritmodules(ss_name,ss_value,directory,filename):
    subprocess.Popen("echo '%s %s' >> %s/%s" %(ss_name, ss_value, directory, filename), shell=True, stdout=subprocess.PIPE).communicate()
    return

def export_i_names(ss_ilname):
    if IRREGULARITY_I_NAME.has_key(ss_ilname):
    	return IRREGULARITY_I_NAME[ss_ilname]
    else:
    	return ss_ilname.replace("ss_","i_")

def usage():
    print "Usage: python checkout.py -s <subsystem> [-d <target_directory>] [-p <product>] [-r <svn_root_url>] [-t <svn_trunk/branch_directory>] [-b <branch_name>] [-f <freezed_tag]"
    print "If product is not defined, 'IL' will be used. If target is not defined, '.' will be used."
    print "<svn_root_url> and <svn_trunk/branch_directory> defaults are different for different products."
    print "<branch_name> default is 'TRUNK'. A section with this name must be found in conf/<product>.cfg file."
    print "\nE.g.:"
    print "python checkout.py -s SS_ILCallMgmt -p IL -d temp_folder -r https://svne1.access.nsn.com -t isource/svnroot/scm_il/trunk/ipal-main-beta -b TRUNK\n"
    print "\nRCP trunk:"
    print "python checkout.py -s SS_ILCallMgmt -p vrnc -d temp_folder\n"
    print "\nCloudIL trunk for vbgw:"
    print "python checkout.py -s SS_ILCallMgmt -p vbgw -d temp_folder\n"
    print "python checkout.py -s rcploglib -p rcp -d rcploglib_trunk\n"
    print "\nRCP wlc tag:"
    print "python checkout.py -s rcploglib -p rcp -d rcploglib_from_tag --ft RCP_WLC_15.35.0\n"
    print "\nRCP rcp_common build tag :"
    print "python checkout.py -s rcploglib -p rcp -d rcploglib_another_tag --ft rcp_common/RCP_2015-08-28_06-00-00\n"
    print "\nRCP rcp_bts build tag :"
    print "python checkout.py -s rcploglib -p rcp -d rcploglib_another_tag --ft rcp_bts/RCP_BTS_15.34.0\n"
    print "\nRCP rcp_rnc build tag :"
    print "python checkout.py -s rcploglib -p rcp -d rcploglib_another_tag --ft rcp_rnc/RCP_RNC_15.34.0\n"

if __name__ == "__main__":
    (options, args) = parser.parse_args(sys.argv)

    if not options.ss_names:
        print "\nERROR: Subsystems not defined!"
        usage()
        sys.exit(1)

    if options.product:
        product = options.product
    else:
        product = "IL"

    if options.branch_name:
        branch_name = options.branch_name
    elif options.tag_name:
        #branch_name = options.tag_name
        branch_name = "TAGS"
    else:
        branch_name = "TRUNK"

    svn_trunk, svn_root, subsystems_raw = format_product(product.lower(), branch_name)
    subsystems_to_checkout = set(subsystems_raw)

    if options.svn_trunk: # Overwrite if given with -t
        svn_trunk = options.svn_trunk

    if options.svn_root: # Overwrite if given with -r
        svn_root = options.svn_root

    if options.tag_name: # Overwrite if given with -f
        svn_trunk = "%s%s/" %(svn_trunk, options.tag_name)

    svn_dir = "%s/%s" %(svn_root, svn_trunk)

    print "Product:", product.upper()
    print "SVN dir: %s" %svn_dir
    dependency_graph = fetch_dependency_graph(product, svn_dir, options)
    if product == 'rcp' or product == 'vrnc' or product == 'vbgw':
         svn_externals, git_externals = fetch_externals(product, dependency_graph, svn_dir, options, True)
    else:
        svn_externals, git_externals = fetch_externals(product, dependency_graph, svn_dir, options, False)
    directory = "."
    if options.directory:
        directory = options.directory
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    print "Checking out to %s" % directory

    subsysytem_to_checkout_base = subsystems_to_checkout.copy()
    for ss_name in options.ss_names.split(","):
        subsystems_to_checkout |= resolve_dependencies(ss_name, dependency_graph, subsystems_to_checkout)
    
    subprocess.Popen("test -f %s/gerrit_code/external_files && rm %s/gerrit_code/external_files" %(directory,directory), shell=True, stdout=subprocess.PIPE).communicate()
    subprocess.Popen("mkdir -p %s/gerrit_code" %directory, shell=True, stdout=subprocess.PIPE).communicate()
    for ss_ilname in subsystems_to_checkout.copy():
        if ss_ilname in SUBSYSTEM_GIT_LIST or ss_ilname.startswith("ss_il") or ss_ilname.startswith("ss_rcp"):
            i_ilname = export_i_names(ss_ilname)
            if svn_externals.has_key(i_ilname):
                export_gerritmodules(svn_externals[i_ilname].split(' ')[1],svn_externals[i_ilname].split(' ')[0],directory,"gerrit_code/external_files")
                try:
                    subsystems_to_checkout.remove(i_ilname)
                except:
                    pass
            try:
               subsystems_to_checkout.remove(ss_ilname)
               if svn_externals.has_key(ss_ilname):
               	   export_gerritmodules(svn_externals[ss_ilname].split(' ')[1],svn_externals[ss_ilname].split(' ')[0],directory,"gerrit_code/external_files")   
               else:
                   export_gerritmodules(git_externals[ss_ilname].split(' ')[0],git_externals[ss_ilname].split(' ')[1],directory,"gerrit_code/external_files")
            except:
               pass
        
        
    for ss_name in subsystems_to_checkout:
        if svn_externals.has_key(ss_name):
            target_dir = os.path.join(directory, svn_externals[ss_name].split(' ')[0])
            sys.stdout.write("Checking out %s to %s from SVN...\n" % (svn_externals[ss_name].split(' ')[0], target_dir))
            sys.stdout.flush()
            
            try:
                url = "%s%s" % (svn_root, svn_externals[ss_name].split(' ')[1])
                print url
                ss = re.search(r'[^\/]+$', url).group(0)
                branch = url[:-len(ss)]
                branch_list = svn_list_branch(branch).splitlines()               
                counter = 0
                for line in branch_list: #Jsi, for interface checkout
                   if line.startswith('SS_') or line.startswith('I_'):
                       target_dir = os.path.join(directory, line)
                       counter += 1
                       svn_checkout(branch+line, target_dir)
                       print("Checked out " + line[:-1])
                if counter == 0:
                    svn_checkout(url, target_dir)
                sys.stdout.write(" OK\r\n")
            except RuntimeError:
                sys.stdout.write(" FAILED\r\n")        
            sys.stdout.flush()
            if ss_name.startswith('ss_'):
               interface_name = ss_name.replace('ss_', 'i_')
            else:
               interface_name = 'no_ss'
            if ss_name.startswith('ss_rcp'):
               rcp_interface_name = ss_name.replace('ss_rcp', 'i_')
            else:
               rcp_interface_name = 'no_rcp_ss'
                      
        elif git_externals.has_key(ss_name):
            target_dir = os.path.join(directory, ss_name)
            sys.stdout.write("Checking out %s to %s from GIT..." % (ss_name, target_dir))
            sys.stdout.flush()
            
            try:
                url, branch = git_externals[ss_name].split()
                if options.git_https == True:
                    sys.stdout.write("\n")
                    output = git_checkout(url, branch, target_dir, True)
                else:
                    output = git_checkout(url, branch, target_dir)
                if output[0] != "":
                    sys.stdout.write(" FAILED:\n%s \r\n" % output[0])
                elif output[1] != "":
                    sys.stdout.write(" FAILED:\n %s \r\n" % output[1])
                else:
                    sys.stdout.write(" OK\r\n")
            except RuntimeError:
                sys.stdout.write(" FAILED\r\n")
                
            sys.stdout.flush()
        else:
            print "WARN: Could not resolve location for %s. Add the location to svn:externals property." % ss_name
            
            print "Cloning from gerrit...."    
    print "%s/git_rcpco.sh %s %s %s" %(sys.path[0],directory,options.ss_names,options.gerrit_refspec)
    stdout,stderror = subprocess.Popen("%s/git_rcpco.sh %s %s %s" %(sys.path[0],directory,options.ss_names,options.gerrit_refspec), shell=True, stdout=subprocess.PIPE).communicate() 
    print stdout


