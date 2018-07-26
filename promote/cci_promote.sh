#!/bin/bash
ls -al

#for testing ###
# export WORKSPACE="../workspace"
# branch="common"
# subsystem="SS_ILSymCollector"
# export tool="../../svn-citools/src/PCIQueue.py"
# export db="ilcidashboarddev"
############

rev_vt="$WORKSPACE/mcrnc/logs/rev.txt"
rev_cld="$WORKSPACE/cloud/logs/rev.txt"

il_change_file="$WORKSPACE/mcrnc/logs/testcases.txt"
cloud_change_file="$WORKSPACE/cloud/logs/testcases.txt"
testcase_change_file="$WORKSPACE/testcases.txt"

export tool="/linux_builds/hzci/apps/pciqueue/PCIQueue.py"
export db="ilcidashboard"

>$testcase_change_file
function contact_files(){
	for var in "$@";do
		if [ -f "$var" ];then
			cat "$var" >>$testcase_change_file
		fi
	done
}

contact_files "$il_change_file" "$cloud_change_file"

# git clone ssh://jenkins_CCI@gerrit.nsn-net.net:29418/citools/cciscript
gerrit_py="../common/gerrit.py"

cat $rev_vt
echo "**************"
cat $rev_cld

testcase_changes=`cat $testcase_change_file|sort|uniq`

isstopfix=$(python $tool stopfix get --db $db)
additional_dep=stop_fix
svnroot="https://svne1.access.nsn.com/isource/svnroot"

REVIEW_ERROR=99
SUBMIT_ERROR=100

function submit_testcase_change(){
    testcase_change=$1
    is_mergeable=$(python $gerrit_py query -c $testcase_change -f mergeable)
    if [ "$is_mergeable" == "True" ];then
      #set code-review and verified
      python $gerrit_py review --change $testcase_change --code_review +2 --verified +1
      if [ $? -ne 0 ];then
        echo "Meet an error when setting code-review and verified flag for change $testcase_change"
        exit $REVIEW_ERROR
      else
        echo "Start submit change $testcase_change"
        python $gerrit_py submit -c $testcase_change
        if [ $? -ne 0 ];then
          echo "Meet an error when submit change $testcase_change"
          exit $SUBMIT_ERROR
        fi
      fi
    fi
}

testcase_db_value="" ## like @12345@11092
function get_testcase_db_value(){
  for testcase in $testcase_changes;do
    if [ ! -z "$testcase" ];then
      testcase_db_value="$testcase_db_value@$testcase"
    fi
  done
}

get_testcase_db_value
echo "testcase_db_value=$testcase_db_value"

function push()
{
  cfgfile=$1
  subsystem=$2
  branch=$(cat $cfgfile|sort|uniq|grep "^$subsystem "|cut -d " " -f2)
  version=$(cat $cfgfile|sort|uniq|grep "^$subsystem "|cut -d " " -f3|sed "s/r//g")
  
  IFS=$'\n';for i in $(cat $cfgfile|sort|uniq|grep -v "^$subsystem ");do
    sub=$(echo $i|cut -d " " -f1)
    brc=$(echo $i|cut -d " " -f2)
    ver=$(echo $i|cut -d " " -f3|sed "s/r/@/g")
    depfrom=$svnroot/$sub/$brc
    depto=$(echo $depfrom|sed s#branches/VirtualTrunk.*#trunk#g|sed s#cloudVT.*#cloudILtrunk#g|sed s#cloudILtrunk.*#cloudILtrunk#g)
    deplstver=$(svn log -l1 $depto --username=hzscm  --password=ZqvonUKw --no-auth-cache --trust-server-cert --non-interactive|grep -oE "^r[0-9]+"|grep -oE [0-9]+)
    echo "$depfrom"
    echo "$depto"
    echo "$deplstver"
    if test $(echo $ver|grep -oE [0-9]+) -gt $deplstver;then
    	deps=$sub/$brc/$sub$ver:$deps
    fi
  done

  deps=$(echo $deps|sed s/:$//g|sed "s/\s//g")
  
  
  if test $deps;then DEP="-D$deps";fi
  
  if [ ! -z "$testcase_db_value" ];then
    testcase_cmd="-T$testcase_db_value"
  fi
  
  echo "python $tool push $subsystem/$branch/$subsystem $version $testcase_cmd $DEP --db  $db "

  python $tool push $subsystem/$branch/$subsystem $version $testcase_cmd $DEP --db $db  
  if [ $? -ne 0 ];then
    echo "Error: promote failed!!!"
    exit $?
  fi
  
}


if [ "`echo $branch`" == "cloud" ];then
  push $rev_cld $subsystem
elif [ "`echo $branch`" == "il" ];then
  push $rev_vt $subsystem
else
  push $rev_vt $subsystem
  push $rev_cld $subsystem
fi 


lst=$(python $tool popall --db  $db)
if [ $? -ne 0 ];then
  echo "Error: python $tool popall --db  $db failed!!!"
  exit $?
fi

auth=
for new_i in $(echo "$lst"|sed "s/\s/,/g"|cut -d "," -f1,4);do
   i=$(echo $new_i|cut -d "," -f1)
   j=$(echo $new_i|cut -d "," -f2)
   echo "i=$i"
   echo "j=$j"
   sub=$(echo $i|cut -d "/" -f1)   
   from=$svnroot/$(echo $i|sed s#/$sub##g)
   to=$svnroot/$(echo $i|cut -d "@" -f1|sed s#branches/VirtualTrunk.*#trunk#g|sed s#cloudVT.*#cloudILtrunk#g|sed s#cloudILtrunk.*#cloudILtrunk#g|sed s#noSuchBranches#branches#g) 
   echo "svn del $to  -m [*PCI AUTO COMMIT*]"
   svn del  $to --username=hzscm  --password=ZqvonUKw --no-auth-cache --trust-server-cert --non-interactive -m "[*PCI AUTO COMMIT*]"   
   echo "svn cp $from $to -m [*CCI AUTO COMMIT*] svn cp $from to $to "
   svn cp $from $to --username=hzscm  --password=ZqvonUKw --no-auth-cache --trust-server-cert --non-interactive  -m "[*CCI AUTO COMMIT*] svn cp $from to $to"

   if [ "N/A" != "$j" ];then
      to_submit_changes=$(echo $j| tr "@" "\n")
      for to_submit_change in $to_submit_changes;do
      	if [ -z "$to_submit_change" ];then
      		continue
      	fi
      	echo "submit change $to_submit_change ..."
        submit_testcase_change $to_submit_change
      done
   fi 
done
