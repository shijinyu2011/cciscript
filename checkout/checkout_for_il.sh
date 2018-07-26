#!/bin/bash 
subsystem=$1
refs=$2
VARENT=$3
workspace=$4
logpath=$5

check_sack(){
   df -h | grep "/McBED/sacks"
   if [ $? -ne 0 ];then
      echo "sack is not mounted, now go to mount sack"
      mount hzeesn10.china.nsn-net.net:/vol/hzeesn10_bin/ee_pdeswb /McBED/sacks
      if [ $? -ne 0 ];then
         echo "Error, sack mount failed,exit"
         exit 1
      fi
    fi
}

echo "check sack mount"
check_sack
#logpath="`pwd`"
common="svn:externals"
auth="--username hzci --password b2a6eefb --non-interactive --trust-server-cert "
export revtext="$logpath/rev.txt"
ciscript=$(cd $(dirname $0);pwd)
extfile="$workspace/gerrit_code/external_files"
codepath="$workspace/gerrit_code"
if ! test $STATIC_SCRIPT_ROOT;then export STATIC_SCRIPT_ROOT=/home/hzci/hudson-cci/ci3_scripts;fi
mkdir -p $codepath

case $VARENT in
   "wr-mips-6wind") value="--product rnc -w -a mips -g w";;
   "wr-mips-56xx") value="--product rnc -w -a mips -g b";;
   "wr-mips-6wind-56xx")  value="--product rnc -w -a mips -g v";;
   "wr-mips-filb-6wind")  value="--product rnc -w -a mips -g f";;
   "wr-ppc-default") value="--product rnc -w -a ppc";;
   "wr-ppc-scnam")  value="--product rnc -w -a ppc -g s";;
   "wr-x86_64-default") value="--product rnc -w -a x86_64";;
   "wr-mips-default-6wind") value="--product rnc -w -a mips";;
   "wr-mips-6wind-bmpp") value="--product rnc -w -a mips -g m";;
   "wr-mips-bmpp")  value="--product rnc -w -a mips -g p";;
   "wr-mips-filb")  value="--product rnc -w -a mips -g f";;
   "wr-ppc-adsp1")  value="--product rnc -w -a ppc -g c";;
   "wr-mips-default") value="--product rnc -w -a mips";;
   "wr-x86_64-acpi5") value="--product rnc -w -a x86_64 -g i";;
   "wr-ppc-adsp2")  value="--product rnc -w -a ppc -g d";;
   "wr-mips-6wind-ampp2") value="--product rnc -w -a mips -g a";;
   "test-x86") value="--product rnc -a x86_64";
               PRODUCT=ipalite;
               type=ut;;
   "static-analysis")value="-w";
               PRODUCT=ipalite;
               type=static;;
   "test-cloud") export PRODUCT=cloudil;
               type=ut;;
   "static-analysis-cloud") export PRODUCT=cloudil;
               type=static;;
   "wr-clouldil") export PRODUCT=cloudil;;
   *) value="-w";;
esac

if [ "`echo $PRODUCT`" = "cloudil" ];then
   special="cloudilsvn:externals"
   svn_externals="https://svne1.access.nsn.com/isource/svnroot/scm_il/trunk/ipal-main-beta"
   value="-p vrnc"
   if ! test $new_brc;then new_brc="branches/cloudVT";fi
   if ! test $old_brc;then old_brc="branches/cloudILtrunk";fi
   rpms="build/*.rpm"
else
   special="legacyilsvn:externals"
   svn_externals="http://svne1.access.nsn.com/isource/svnroot/scm_il/trunk/ipal-main-beta"
   if ! test $new_brc;then new_brc="branches/VirtualTrunk";fi
   if ! test $old_brc;then old_brc="trunk";fi
   rpms="build/*.rpm"
fi
echo "clean workspace"
cd $workspace 
ls |grep -v gerrit_code|xargs rm -fr 
cd -

svn pg $common $auth $svn_externals|grep -v "\(mgw\)\|\(bgw\)\|\(SS_ILFT\)" > $extfile
svn pg $special $auth $svn_externals|grep -v "\(mgw\)\|\(bgw\)\|\(SS_ILFT\)" >> $extfile

if [ "`echo $PRODUCT`" = "cloudil" ];then 
    subs="SS_DPDK SS_TestUtil build flexiserver fvntools"
    for i in $(echo $subs);do
      echo "git clone ssh://hzci@gerrite1.ext.net.nokia.com:8282/scm_rcp/$i -b rcptrunk ${workspace}/$i"
      git clone ssh://hzci@gerrite1.ext.net.nokia.com:8282/scm_rcp/$i -b rcptrunk ${workspace}/$i
    done
    echo "ln -snf ${workspace}/SS_TestUtil/I_TestUtil/I_TestUtil ${workspace}/I_TestUtil"
    ln -snf ${workspace}/SS_TestUtil/I_TestUtil ${workspace}/I_TestUtil

   # echo "/isource/svnroot/SS_ILThirdpart/branches/cloudILtrunk/SS_ILThirdpart SS_ILThirdpart">>$extfile
fi


#echo "get dependency for $subsystem"
#cmd="select Subsystem from il_ci_dashboard_group  where GroupName != 0 and Subsystem <> '$subsystem' and GroupName=(select GroupName from il_ci_dashboard_group where Subsystem='$subsystem')"
host="eclipseupd.china.nsn-net.net"
db="ilcidashboard"
#depends=$(ssh eclipse@$host "mysql -uhzci -phzci $db -s -e \"$cmd\""|grep -v "Subsystem")

    module=$subsystem
	host="hzdatav01.china.nsn-net.net" 
	db="ilcidashboard"
	
	cmd="select Subsystem from il_ci_dashboard_group  where GroupName != 0 and Subsystem <> '$module' and GroupName=(select GroupName from il_ci_dashboard_group where Subsystem='$module')"
    depends=$(ssh eclipse@eclipseupd.china.nsn-net.net "mysql -uroot -pILMAN@db -hhzdatav01.china.nsn-net.net ilcidashboard -s -e \"$cmd\""|grep -v "Subsystem")



## SS_ILDmxMsg cloud branch need compile SS_RCPMsgTool
if [ "${subsystem}" == "SS_ILDmxMsg" ] && [ "$PRODUCT" == "cloudil" ];then
    depends="$depends SS_RCPMsgTool"
fi


#dependency can be initial in the env
if ! test $isbranch;then
    for i in $(echo $depends);do cat $workspace/gerrit_code/external_files|grep $i && dependency=$(echo $dependency $i);done
fi
#dependency=$(mysql --host=$host -uhzci -phzci $db -s -e "$cmd"|grep -v "Subsystem")

echo "[info]dependency is $dependency"

echo "get sack version"
cmd="select Sack from il_ci_dashboard_group where Subsystem='$subsystem'"
ischange=$(ssh eclipse@$host "mysql -uhzci -phzci $db -s -e \"$cmd\""|grep "imenv/0")
#ischange=$(mysql --host=$host -uhzci -phzci $db -s -e "$cmd"|grep "imenv/0")

cmd="select concat(name,'=',value) from il_ci_dashboard_globalvariable where name like '%env%'"
latest_sackversion=$(ssh eclipse@$host "mysql -uhzci -phzci $db -s -e \"$cmd\""|grep imenv|cut -d "=" -f2)
#latest_sackversion=$(mysql --host=$host -uhzci -phzci $db -s -e "$cmd"|grep imenv|cut -d "=" -f2)

#export isVT=true
echo "checkout code"
echo $preconfig >> $workspace/gerrit_code/external_files
echo "$ciscript/git_rcpco.sh $workspace $subsystem,$(echo $dependency|tr ' ' ',') $refs"
for i in $(echo $dependency $dependency_env);do

   sed -i "s#/$i/$old_brc#/$i/$new_brc#g" $workspace/gerrit_code/external_files

   #workround for common subsystems, replace trunk to branches/VirtualTrunk
   sed -i "s#/$i/trunk#/$i/branches/VirtualTrunk#g" $workspace/gerrit_code/external_files

done

########################


$ciscript/git_rcpco.sh $workspace $subsystem $refs

echo "record related subsystems test version"
for subname in $(echo $subsystem $dependency);do
    git --git-dir=$codepath/$subname/.git --work-tree=$codepath/$subname log -1
    bch=$(git --git-dir=$codepath/$subname/.git --work-tree=$codepath/$subname log -1|grep -v "\[.* Notes:"|grep -A2 Notes:|grep -v Notes|sed "s/^ *//g"|cut -d " " -f2)
    ver=$(git --git-dir=$codepath/$subname/.git --work-tree=$codepath/$subname log -1|grep -v "\[.* Notes:"|grep -A2 Notes:|grep -v Notes|sed "s/^ *//g"|cut -d " " -f1)
    gitver=$(git --git-dir=$codepath/$subname/.git --work-tree=$codepath/$subname log -1|grep ^commit|cut -d" " -f2)
    echo "$subname $bch $ver $gitver" >> $revtext
done


# ssh root@10.68.165.226 "mkdir -p /data/www-root/cloudil/$subsystem/images/yaml;\ 
# cp -fr /data/www-root/cloudil/yaml/ /data/www-root/cloudil/$subsystem/images"


if [ "`echo $PRODUCT`" == "cloudil" ] && test -z $GERRIT_BRANCH;then
  echo "ready to scp yaml file to 10.68.165.226 server"
  if cat $revtext |grep "\(SS_ILTestDeployment\)\|\(SS_ILDeployment\)";then 
    echo "upload yaml and env from SS_ILTestDeployment"
    echo "get yaml from testdeployment to 10.68.165.226 server" 
    ssh root@10.68.165.226 "mkdir -p /data/www-root/cloudil/$subsystem/images/yaml"
    pushd $codepath/SS_ILTestDeployment/SS_ILTestDeployment/new_yaml/IL_vRNC_specific
#      scp ./IL_vRNC.yaml root@10.68.165.226:/data/www-root/cloudil/$subsystem/images/yaml/IL_vRNC_Max.yaml
      tar czvf cloudil-heat-templates.tgz  IL_vRNC.yaml IL_vRNC.env read.me modules/
      scp ./cloudil-heat-templates.tgz root@10.68.165.226:/data/www-root/cloudil/$subsystem/images/yaml/
      rm -f cloudil-heat-templates.tgz
    popd
  else
    echo "when compile other subsystem scp yaml file from basepackage server to 10.68.165.226 server"

    triggerfile="https://gitlabe1.ext.net.nokia.com/ILCI/trigger/raw/master/cloudil/latest_ok_smoke_tested/cloudil_smk_ok_trigger.txt"
    curl -k -s $triggerfile  -o trigger_file_txt
    if [ $? -ne 0 ];then
        echo "curl -s $triggerfile  -o trigger_file_txt failed, exit"
        exit 2
    fi

    echo "--trigger file content --"
    cat trigger_file_txt
    echo "-- trigger file end --"
    image_url=$(cat trigger_file_txt| grep -Po 'image_url=\K.+')
    heat_template=$(cat  trigger_file_txt| grep -Po 'heat_template\K.+')
    build_id=$(cat trigger_file_txt|grep -Po 'build_id=\K.+')


    echo "get heat template file : wget -q ${image_url}/yaml/cloudil-heat-templates.tgz"
    wget -q ${image_url}/yaml/cloudil-heat-templates.tgz

    if [ ! -f cloudil-heat-templates.tgz ];then
      echo "[error]could not download heat template file from ${image_url}/yaml"
      exit 1
    fi

#    tar xzf cloudil-heat-templates.tgz
#    mv IL_vRNC_env.txt IL_vRNC.env
#    mv IL_vRNC.yaml IL_vRNC_Max.yaml
#    rm -f cloudil-heat-templates.tgz
#    tar czvf cloudil-heat-templates.tgz  IL_vRNC.env IL_vRNC.yaml modules/

    echo "ssh root@10.68.165.226 \"mkdir -p /data/www-root/cloudil/$subsystem/images/yaml\""
    ssh root@10.68.165.226 "mkdir -p /data/www-root/cloudil/$subsystem/images/yaml; \
    cd /data/www-root/cloudil/$subsystem/images/yaml;rm -f *.yaml *.tgz *.txt"
    echo "upload yaml file "
#    scp ./IL_vRNC_Max.yaml root@10.68.165.226:/data/www-root/cloudil/$subsystem/images/yaml/
    scp ./cloudil-heat-templates.tgz root@10.68.165.226:/data/www-root/cloudil/$subsystem/images/yaml/
  fi
fi

echo "get depend testcase"
deps=`git --git-dir=$codepath/$subsystem/.git --work-tree=$codepath/$subsystem log -1|grep "\[DEPENDS.*:.*\]"|grep -Eo "T[0-9]+"|cut -b 2-`
echo $deps > $logpath/testcases.txt;

cd $workspace
if test $ischange;then
  if [ -z $latest_sackversion ];then
    echo "cloud not get sack version. skip replace."
  else
   sed -ri "s/imenv.*[0-9]+/imenv $latest_sackversion/g" product/build/config_version.source
  fi
fi


if [ "`echo $type`" = "ut" ];then
  echo "make test"
  echo "product/build/svnenv.sh --product rnc $value -j make test -C $subsystem/build"
  logfile="ut.log"
  ut_log="product/build/TESTS-TestSuites.xml"
  coverage_log="$subsystem-coverage.xml"
  rm -fr $logpath/statistics
  export VARENT="test-x86"
  product/build/svnenv.sh $value -j "$ciscript/subut.sh $subsystem ${coverage_log}" > $logpath/$logfile 2>&1
  test -e $ut_log && cp -f $ut_log $logpath/
  test -e  $subsystem/$coverage_log && cp -f  $subsystem/$coverage_log $logpath/
  cd $STATIC_SCRIPT_ROOT
   ./il_static_check.sh $PRODUCT  $subsystem $workspace $logpath/statistics
  rst=$? 
#  ./il_static_check.sh ipalite $subsystem $workspace $logpath/statistics
#elif [ "`echo $VARENT`" = "test-cloud" ];then
#  logfile="ut.log"
#  ut_log="product/build/TESTS-TestSuites.xml"
#  export V=t
#  export PATH=$PATH:/apps/klocwork/bin
#  python $WORKSPACE/sad-runner/sad_runner.py -p cloudil -m $subsystem -b $workspace/$subsystem -o $logpath
#  test -e $ut_log && cp -f $ut_log $logpath/
elif [ "`echo $type`" = "static" ];then
  cd $STATIC_SCRIPT_ROOT
  export PATH=$PATH:/apps/klocwork/bin
  export VARENT="static-analysis"
   ./il_static_check.sh $PRODUCT $subsystem $workspace $logpath/statistics
   rst=$?
#   ./il_static_check.sh ipalite $subsystem $workspace $logpath/statistics
#elif [ "`echo $VARENT`" = "static-analysis-cloud" ];then
#  export V=s
  export PATH=$PATH:/apps/klocwork/bin
#  python $WORKSPACE/sad-runner/sad_runner.py -p cloudil -m $subsystem -b $workspace/$subsystem -o $logpath
#  rst=$?
else
  echo "make compile"
  echo "product/build/svnenv.sh $value -j $ciscript/submake.sh $subsystem $(echo $dependency)"
  logfile="compile.log"
  product/build/svnenv.sh $value -j "$ciscript/submake.sh $subsystem $(echo $dependency)" > $logpath/$logfile 2>&1
  for i in $(echo $subsystem $dependency);do
    cp -r $workspace/$i/$rpms $logpath/
  done
  rst=0
fi

if [ "$VARENT" = "test-x86" ];then
  cat $logpath/$logfile |grep "AssertionError:" && exit 1
fi

if echo $VARENT|grep -v "static-analysis";then
  echo "check result"
  cat $logpath/$logfile |grep ": \*\*\*" && exit 1
  if ! test -f $logpath/$logfile;then echo "$logpath/$logfile not found";exit 1;fi
        if test -f $logpath/TESTS-TestSuites.xml;then cat $logpath/TESTS-TestSuites.xml|grep -E \(errors=.[1-9]+\)\|\(failures=.[1-9]+\) && exit 1;fi
        exit $rst
else
     exit $rst
fi


