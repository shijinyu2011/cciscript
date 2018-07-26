#!/bin/bash
gerrit_server=$GERRIT_SERVER
gerrit_server_port=$GERRIT_PORT

il_change_file="$WORKSPACE/mcrnc/logs/testcases.txt"
cloud_change_file="$WORKSPACE/cloud/logs/testcases.txt"
testcase_change_file="$WORKSPACE/testcases.txt"

export tool="PCIQueue.py"
export db="ilcidashboard"
# branch golabl variable Passed from the environment variables. reset by getBranchInfo

function _exit(){
  ret=$1
  exit $ret
}
function getTrunkVersion(){
  sub=$1
  sub_dir="$WORKSPACE/$branch/$sub"
  rev=`git --git-dir=$sub_dir/.git log origin/$trunk --oneline | head -1 | cut -d " " -f1`
  echo $rev
}
function checkSubExist(){
  sub=$1
  sub_dir="$WORKSPACE/$branch/$sub"
  if [ ! -d "$sub_dir" ];then
    mkdir -p $sub_dir
    # git clone ssh://hzci@$gerrit_server:$gerrit_server_port/scm_il/$sub $sub_dir
    git init $sub_dir
    git --git-dir=$sub_dir/.git remote add origin ssh://hzci@$gerrit_server:$gerrit_server_port/scm_il/$sub
  fi
  echo "git --git-dir=$sub_dir/.git fetch origin $trunk $branch"
  git --git-dir=$sub_dir/.git fetch origin $trunk $branch
  [  $? -eq 0 ] || _exit 1
}

function mergeToTrunk(){
  sub=$1
  commitid=$2
  push_opt=$3
  sub_dir="$WORKSPACE/$branch/$sub"

  git --git-dir=$sub_dir/.git log origin/$trunk --oneline | grep "$commitid"
  if [ $? -ne 0 ];then #need  push 
    if [ -z "$push_opt" ];then
      git --git-dir=$sub_dir/.git reset HEAD --hard
      git --git-dir=$sub_dir/.git clean -df
      echo "git --git-dir=$sub_dir/.git checkout origin/$trunk"
      git --git-dir=$sub_dir/.git checkout origin/$trunk
      [  $? -eq 0 ] || _exit 1

      echo "git --git-dir=$sub_dir/.git merge $commitid -m \"merge $commitid to origin/$trunk\""
      git --git-dir=$sub_dir/.git merge $commitid -m "merge $commitid to origin/$trunk"
      [  $? -eq 0 ] || _exit 1

      echo "git --git-dir=$sub_dir/.git push origin HEAD:$trunk"
      git --git-dir=$sub_dir/.git push origin HEAD:$trunk
      [  $? -eq 0 ] || _exit 1
    else
      echo "git --git-dir=$sub_dir/.git push origin $commitid:refs/heads/$trunk $push_opt"
      git --git-dir=$sub_dir/.git push origin $commitid:refs/heads/$trunk $push_opt
      [  $? -eq 0 ] || _exit 1
    fi
  else
    echo "$commitid has been in $trunk, skip duplicate push!!!"
  fi
}

function push()
{
  cfgfile=$1
  subsystem=$2
  branchinfo=$(cat $cfgfile|sort|uniq|grep "^$subsystem "|cut -d " " -f2)
  version=$(cat $cfgfile|sort|uniq|grep "^$subsystem "|cut -d " " -f4| cut -b1-8)

  IFS=$'\n';for i in $(cat $cfgfile|sort|uniq);do
    sub=$(echo $i|cut -d " " -f1)
    brc=$(echo $i|cut -d " " -f2)
    ver=$(echo $i|cut -d " " -f4| cut -b1-8)
    checkSubExist "$sub"
    if [ "$sub" != "$subsystem" ];then
      sub_dir="$WORKSPACE/$branch/$sub"
      trunk_Version=`getTrunkVersion $sub`
      branch_version=$(echo $ver | cut -b1-7)
      echo "branch_version=$branch_version, trunk_Version=$trunk_Version"
      git --git-dir=$sub_dir/.git log $trunk_Version --oneline | grep "$branch_version"
      if [ $? -ne 0 ];then
        deps="${sub}/${brc}/${sub}@${ver}:${deps}"
      else
        echo "${sub}'s branch_version $branch_version already in trunk_Version $trunk_Version!!!"
      fi
    fi
  done

  deps=$(echo $deps|sed s/:$//g|sed "s/\s//g")
  if test $deps;then DEP="-D$deps";fi
  if [ ! -z "$testcase_db_value" ];then
    testcase_cmd="-T$testcase_db_value"
  fi
  
  if [ "$force_push" = "false" ];then
      echo "===================PUSH TO ilcidashboard start==================="
      echo "python $tool push $subsystem/$branchinfo/$subsystem $version $testcase_cmd $DEP --db  $db "
      python $tool push $subsystem/$branchinfo/$subsystem $version $testcase_cmd $DEP --db $db
      ret=$? 
      if [ $ret -ne 0 ];then
        echo "Error: promote failed!!!"
        _exit $ret
      fi
      echo "python $tool check $subsystem/$branchinfo/$subsystem $version  --db  $db"
      lst=$(python $tool check $subsystem/$branchinfo/$subsystem $version  --db  $db)
      ret=$?
      if [ $ret -ne 0 ];then
        echo -e "\nError: $subsystem 's dependence:$DEP cci not PASS, pls check.\n"
        _exit $ret
      fi
      echo "$lst"
      push_opt=""
      echo "===================PUSH TO ilcidashboard finished==================="
  else
      push_opt="-f"
  fi

  IFS=$'\n';for i in $(cat $cfgfile|sort|uniq);do
    sub=$(echo $i|cut -d " " -f1)
    git_version=$(echo $i|cut -d " " -f4|cut -b 1-7)
    echo "mergeToTrunk $sub $git_version $push_opt"
    mergeToTrunk $sub $git_version $push_opt
  done
}
function getBranchInfo(){
  type=$1
  if [ "`echo $type`" == "il" ];then
    rev_file="$WORKSPACE/mcrnc/logs/rev.txt"
    branch=${VirtualTrunk:-VirtualTrunk}
    trunk=${ILTrunk:-master}
  elif [ "`echo $type`" == "cloud" ];then
    rev_file="$WORKSPACE/cloud/logs/rev.txt"
    branch=${cloudVT:-cloudVT}
    trunk=${cloudILtrunk:-cloudILtrunk}
  else
    echo "$type is unavailable !!"
    _exit 1
  fi
  echo "product type is $type"
  echo "branch is $branch"
  echo "trunk is $trunk"
  echo "rev_file is $rev_file"
  echo "==============$rev_file  begin=================================="
  cat $rev_file
  echo "==============$rev_file  end  =================================="
}
function main(){
  if  [ "`echo $branch`" == "common" ];then
    types=("il" "cloud")
  else
    types=("$branch")
  fi
  for type in $types
  do
    getBranchInfo $type
    push $rev_file $subsystem
  done
}
################main()############################################
main
_exit 0