#!/bin/bash
#workround for docker containter 
#release the disk space in host
#fstrim / || echo "not a docker image or failed to clear failes"
###########################

svn_branch="https://svne1.access.nokiasiemensnetworks.com/isource/svnroot/scm_rcp/trunk"

#gerrit_module="cat module_file"
#gerritserver="http://hzgitv01.china.nsn-net.net"
gerritserver="hzscm@hzling48.china.nsn-net.net:/linux_gerrit/gerrit/gitrepos/"
if test -z $1;then 
  workcopy="gerrit_code"
else
  workcopy=$1/gerrit_code
fi
currentpath=`dirname $0`
workroundscript=`cd $currentpath && pwd`/workroundforilgit
fullpath=`cd $workcopy && pwd`
external_files=$fullpath/external_files


function retry_cmd() 
{
  local max_retry=3
  local cur_try=0
  local cmd=$1
  local cmd_if_fail=$2
  if [ ! -z "$cmd" ];then
    while [ $cur_try -lt $max_retry ];do
      eval $cmd && return || eval $cmd_if_fail
      ((cur_try+=1))
      if [ $cur_try -eq $max_retry ];then
        return 119
      fi
    done
  else
    return 110
  fi
}

function git_clean() 
{
  local git_dir=$1
  pushd $git_dir
    git reset --hard
    git clean -dxf
  popd
}

mkdir -p  $workcopy
cd $workcopy
cat $external_files
function clglbsubs() {
   for i in `cat $external_files |grep "git\@gitlab"|cut -d " " -f1|sed "s#.*/##g"|sed "s#\.git##g"`;do
      if test -d "../$i/.git";then
         echo "$i has been cloned"
      else
         rm -fr ../$i
         git init ../$i
         git --git-dir=../$i/.git config remote.origin.url $gerritserver/scm_rcp/$i.git
         echo "* -text">../$i/.git/info/attributes
      fi
      git_clean "../$i"
      git_fetch_cmd="git --git-dir=../$i/.git --work-tree=../$i fetch origin ${GERRIT_BRANCH:-master}"
      retry_cmd "$git_fetch_cmd" "git_clean ../$i" || echo "[FAIL]clone $i failed.";exit 1
      git --git-dir=../$i/.git --work-tree=../$i checkout FETCH_HEAD
   done
}

clglbsubs

gerrit_module=`cat $external_files|grep -v "\#"|grep -v "git\@gitlab"|grep -v "I_"|cut -d "/" -f 4|sort |uniq`

echo "`date`: check code"
tmp_fifofile="/tmp/$$.fifo"
mkfifo $tmp_fifofile
exec 6<>$tmp_fifofile
rm $tmp_fifofile

#thread=15
thread=2
for ((i=0;i<$thread;i++));do 
echo
done >&6
SPECIALSUB="SS_DPDK:,"

function clonesub() {
   subsystem=$1
   cat $external_files|grep svnroot\/$subsystem\/>>rcp_external
   if test -d "$subsystem/.git" ;then
       echo "`date`:$subsystem has been cloned"
   else
       rm -fr $subsystem
       echo "`date`:$subsystem has not been cloned, clone a new one"
       if  [ `echo $subsystem|grep "\(SS_IL\)\|\(SS_FVN\)\|\(SS_QNDPM\)\|\(SS_SGWLM\)\|\(SS_SGWNM\)\|\(SS_SGWStacks\)\|\(SS_SGWLibNMLM\)\|\(SS_TestSCCPuser\)\|\(SS_SignalingFPCM\)\|\(SS_SGWSCLI\)\|\(SS_MOMfsSGW\)\|\(SS_QVFDMacSync\)\|\(SS_CaviumSDK\)"` ];then
	      url="scm_il/"
       elif [ `echo $SPECIALSUB|grep "$subsystem:"` ] ;then
          url=`echo $SPECIALSUB |sed -n 's/,/\n/gp' | sed -n '/$subsystem/p'| sed -n 's/$subsystem://gp'`
       elif [ `echo $subsystem|grep "vgp"` ];then
          url=""
       else
          url="scm_rcp/"
       fi
      echo "git clone server/$url$subsystem $subsystem"
      git init $subsystem
      git --git-dir=$subsystem/.git config remote.origin.url $gerritserver/$url$subsystem.git
      git_conf_cmd="git --git-dir=$subsystem/.git config remote.origin.fetch +refs/svn/map:refs/notes/commits"
      retry_cmd "$git_conf_cmd" "git_clean $subsystem" || (echo "[FAIL]clone $subsystem failed.";exit 1)
      echo "* -text">$subsystem/.git/info/attributes
   fi
}

rm -fr rcp_external
for subsystem in $gerrit_module
do
   read -u6  
  {
    echo "clone $subsystem from gerrit..."
    clonesub $subsystem || {echo "clone $subsystem failed"}
    echo >&6
  }&
done
wait


echo "`date`: set work env for git repo"
function checkoutsub() {
   subsystem=$1
   if [ "`cat rcp_external|grep -m 1 svnroot\/$subsystem\/|grep -o \/trunk\/`" = "/trunk/" ];then
      branch="master"
   else
      branch=`cat rcp_external|grep -m 1 svnroot\/$subsystem\/|cut -d"/" -f6|cut -d" " -f1`
   fi

   echo "`date`: checkout code for $subsystem"
   tmp_cmd="git --git-dir=./$subsystem/.git --work-tree=./$subsystem fetch"
   retry_cmd "$tmp_cmd" || (echo "[FAIL]clone $subsystem failed.";exit 1)
   git_clean "./$subsystem"
   tmp_cmd="git --git-dir=./$subsystem/.git --work-tree=./$subsystem fetch origin $branch"
   retry_cmd "$tmp_cmd" || (echo "[FAIL]clone $subsystem from $branch failed.";exit 1)
   git --git-dir=./$subsystem/.git --work-tree=./$subsystem checkout FETCH_HEAD

   for i in `cat rcp_external|grep svnroot\/\$subsystem\/|cut -d " " -f2`;do
      dname=$(echo $i|sed "s#rnc/##g")
      rname=`cat rcp_external|grep svnroot\/\$subsystem\/.*\$dname|cut -d" " -f1|sed s#.*\/##g|sed "s#@[0-9]*##g"`
      echo "`date`: create soft link for $subsystem/$rname"
      echo "**ln -fs `pwd`/$subsystem/$rname `pwd`/../$dname"
      rm -fr `pwd`/../$dname
      if [ "`echo $subsystem`" = "SS_ILProduct" ];then
          cp -r `pwd`/$subsystem/$rname `pwd`/../$dname
      elif test -d `pwd`/$subsystem/$rname; then 
          ln -fs `pwd`/$subsystem/$rname `pwd`/../$dname
      else
          ln -fs `pwd`/$subsystem `pwd`/../$dname
      fi
   done
}

for subsystem in $gerrit_module
do
 read -u6
{
 checkoutsub $subsystem ||(echo "checkout $subsystem failed")
 echo >&6
}&
done
wait
exec 6>&-

if  [ `echo "$3"` != "None" ];then
    echo "checkout test version"
    i=1
    for REF in `echo $3|sed "s/,/ /g"`;do 
      subname=`echo $2|cut -d "," -f$i `
      if cat $external_files|grep "git\@gitlab.*$subname\.git";then subname="../$subname";fi 
      i=$((i+1))
      git --git-dir=./$subname/.git --work-tree=./$subname fetch origin $REF
      git --git-dir=./$subname/.git --work-tree=./$subname checkout FETCH_HEAD
      #check out dependency from gerrit
      echo $REF|grep -q "refs" && deps=`git --git-dir=./$subname/.git log -1|grep "\[DEPENDS:.*\]"|sed "s/T[0-9]\+//g"|grep -Eo "[0-9]+"`
      if test "$deps"; then
        for dep in $deps;do
          gerritapi="http://hzgitv01.china.nsn-net.net/changes/?q=${dep}&o=CURRENT_REVISION&o=CURRENT_COMMIT&o=CURRENT_FILES&o=DOWNLOAD_COMMANDS"
          depfetch=`curl $gerritapi|grep "Checkout.:"|cut -d '"' -f4|cut -d' ' -f4`
          project=`curl $gerritapi|grep '"project": '|sed "s/.*\///g"|sed 's/.*: "//g'|cut -d '"' -f1`
          if cat $external_files|grep "git\@gitlab.*$project\.git";then project="../$project";fi
          echo "git --git-dir=./$project/.git --work-tree=./$project/ fetch origin $depfetch && git --git-dir=./$project/.git --work-tree=./$project/ checkout FETCH_HEAD"
          tmp_cmd="git --git-dir=./$project/.git --work-tree=./$project/ fetch origin $depfetch"
          retry_cmd "$tmp_cmd" || (echo "[FAIL]clone $project from $depfetch failed.";exit 1)
          git --git-dir=./$project/.git --work-tree=./$project/ checkout FETCH_HEAD
        done 
      fi
    done
fi
echo "set workround for rcp gerrit checkout"
$workroundscript ../




