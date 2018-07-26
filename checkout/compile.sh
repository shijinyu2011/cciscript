#!/bin/bash
#example: ./compile.sh SS_ILEITP Nokia_OS_DEV wr-mips-bmpp ./ ./  false
#
SUBSYSTEM=$1   			#sybsystem name 
REFS=$2        			#subsystem version,should be branch name or gerrit ticket refs
VARENT=$3     			#product type
WORKSPACE=$4   			#workspace 
LOGPATH=$5				#log path
IS_MERGED=$6            #if still on gerrit or has merged into branch

##########################################################################
###########  set type  #########################
case $VARENT in
   "wr-mips-6wind-bmpp")  	export PRODUCT=ipalite;
   							value="--product rnc -w -a mips -g m";
   						 	task="compile";;
   						 	
   "wr-mips-bmpp")  		export PRODUCT=ipalite;
   							value="--product rnc -w -a mips -g p";
   						 	task="compile";;
   						 	
   "test-x86")  			export PRODUCT=ipalite;
   							value="--product rnc -a x86_64";
               			 	task="ut";;
               			 	
   "static-analysis")  		export PRODUCT=ipalite;
   							value="-w";
   							task="static";;
   							
   "test-cloud")  			export PRODUCT=cloudil;
                         	type=ut;
                          value="-p vrnc "
                         	task="ut";;
                         	
   "static-analysis-cloud") export PRODUCT=cloudil;
               				type=static;
               				task="static";;
               				
   "wr-clouldil") 			export PRODUCT=cloudil;
   							value="-p vrnc ";
   							task="compile";;
   							
   *) 						echo "unknow type ,exit 1!"
   							exit 1;;
esac

######################################################
EXITCODE=0
COMMONBRANCH=${VirtualTrunk:-VirtualTrunk}
gitrepo="git@gitlabe1.ext.net.nokia.com:IL_SCM/common_il.git"
svnserver="https://svne1.access.nsn.com"
CONFIG_BRANCH="master" ##git@gitlabe1.ext.net.nokia.com:IL_SCM/common_il.git need always use master

if [ "$PRODUCT" = "cloudil" ];then 
	BRANCH=${cloudILtrunk:-cloudILtrunk}
	DEVBRANCH=${cloudVT:-cloudVT}
	gitrepolst="cloudil_gitrepo.lst"
  fp_config="gitrepo.rcp"
else
    BRANCH=${ILTrunk:-master}
    DEVBRANCH=${VirtualTrunk:-VirtualTrunk}
    gitrepolst="legacyil_gitrepo.lst"
    fp_config="fp_gitrepo.lst"
fi
common_configle="commonil_gitrepo.lst"

ciscript=$(dirname $(readlink -f $0))

auth="--username hzci --password b2a6eefb --non-interactive --trust-server-cert "
configtext="$LOGPATH/config.txt"
fpconfigtest="$LOGPATH/fpconfig.txt"
dependtext="$LOGPATH/dependency.txt"
revtext="$LOGPATH/rev.txt"

echo "[info ] WORKSPACE : $WORKSPACE"
cd $WORKSPACE
mkdir -p $LOGPATH

if ! test ${STATIC_SCRIPT_ROOT};then export STATIC_SCRIPT_ROOT=/home/hzci/hudson-cci/ci3_scripts;fi
coverage_log="${SUBSYSTEM}-coverage.xml"
ut_log="product/build/TESTS-TestSuites.xml"
compilelog="compile.log"
utlog="ut.log"


###########  support multithreading  ########################
tmp_fifofile="/tmp/$$.fifo"
mkfifo $tmp_fifofile
exec 6<>$tmp_fifofile
rm $tmp_fifofile
thread=3
for ((i=0;i<$thread;i++));do 
echo
done >&6
############################################

checkenv(){
   echo "[debug info]:check sack"
   df -h | grep "/McBED/sacks"
   if [ $? -ne 0 ];then
      echo "[debug info]:sack is not mounted, now go to mount sack"
      mount hzeesn10.china.nsn-net.net:/vol/hzeesn10_bin/ee_pdeswb /McBED/sacks
      if [ $? -ne 0 ];then
         echo "[debug info]:Error, sack mount failed,exit"
         exit 1
      fi
    fi
    
    ############### clean configure file ########
    rm -fr $configtext $fpconfigtest $dependtext
    touch $dependtext
    
    chmod +x -R $ciscript/*
    
	echo "[info]  env is ok!"
}
get_fp_modules(){
    echo "[cmd] git archive --format=tar.gz --remote=$gitrepo  $CONFIG_BRANCH ${fp_config} |tar -xzO -f - > ${fpconfigtest}"
    git archive --format=tar.gz --remote=$gitrepo  $CONFIG_BRANCH ${fp_config} |tar -xzO -f - > ${fpconfigtest}
    
    ######### checkout fp modules ####################
    if [ "$PRODUCT" = "cloudil" ];then
      cloudil_fp_modules="SS_TestUtil build flexiserver fvntools"
      for dir in $(echo $cloudil_fp_modules);do
        rm $dir -rf
        item=$(cat ${fpconfigtest} | grep -w "$dir")
        url=$(echo $item|cut -d " "  -f1)
        branch=$(echo $item|cut -d " "  -f2)
        echo "git clone $url -b $branch"
        git clone $url $dir
        git --git-dir=$dir/.git checkout $branch
      done
    else
      for item in $(cat ${fpconfigtest}|grep " rnc/"|sed 's/[ \t]*$//g'|sed 's/^[ \t]*//g'|sed 's/[ ][ ]*/,/g');do 
      read -u6
      {
        url=$(echo $item|cut -d ","  -f1)
        folder=$(echo $item|cut -d ","  -f2)
        folderlink=$(echo $folder |sed "s#rnc/##g")
        rm -fr $folder
        echo "[cmd]svn co -q ${url} $folder"
        svn co -q $auth ${url} $folder
        if [ ! -L $folderlink ];then
          ln -s  $folder $folderlink
        fi
        echo >&6
          }&
      done
      wait
    fi
}
workround_change_git2hzci(){
  repo_file=$1
  sed -i 's#ssh://git@#ssh://hzci@#' $repo_file
  cat $repo_file
}
checkout_inittial_code(){
    echo "[info]  get scm config list!"
    git archive --format=tar.gz --remote=$gitrepo  $CONFIG_BRANCH ${common_configle} |tar -xzO -f - > ${configtext}
    echo "" >> ${configtext} # may don't has /n at the last line
    
    echo "[cmd] git archive --format=tar.gz --remote=$gitrepo  $CONFIG_BRANCH ${gitrepolst} |tar -xzO -f - |grep -v "SS_ILFT">> ${configtext}"
    git archive --format=tar.gz --remote=$gitrepo  $CONFIG_BRANCH ${gitrepolst} |tar -xzO -f - |grep -v "SS_ILFT">> ${configtext}
    
    workround_change_git2hzci ${configtext}
    get_fp_modules
    
    ############# checkout product modules ###############
    for item in $(cat ${configtext} |sed '/^ *$/d'|sed 's/[ \t]*$//g'|sed 's/^[ \t]*//g'|sed 's/[ ][ ]*/,/g'|sort|uniq);do
     read -u6
		{
        url=$(echo $item|cut -d "," -f1)
        ref=$(echo $item|cut -d "," -f2)  #|grep -oi "[a-z\_\/]*"
        sub=$(echo $url|sed "s#.*/##g")
        
        echo "[debug]:subsystem name is $sub"
        echo "[debug]:url ${url}"
        echo "[debug]:ref ${ref}"
        
        git init -q $sub
        git --git-dir=$sub/.git remote|grep -q origin && git --git-dir=$sub/.git remote remove origin
        git --git-dir=$sub/.git remote add origin $url
        echo "* -text" > $sub/.git/info/attributes
        git --git-dir=$sub/.git --work-tree=./$sub fetch -q origin $ref
        git --git-dir=$sub/.git --work-tree=./$sub clean -dxf 
        git --git-dir=$sub/.git --work-tree=./$sub reset --hard
        git --git-dir=$sub/.git --work-tree=./$sub checkout FETCH_HEAD
      	echo >&6
    }&
    done
    wait
    exec 6>&-
    echo "[info]:checkout code finished!"
    
    ##########   switch current sybsystem ############
    git --git-dir=$SUBSYSTEM/.git --work-tree=./$SUBSYSTEM fetch -q origin $REFS
    git --git-dir=$SUBSYSTEM/.git --work-tree=./$SUBSYSTEM reset --hard
    git --git-dir=$SUBSYSTEM/.git --work-tree=./$SUBSYSTEM checkout FETCH_HEAD
    
    ###########  add workround  ######################
    rm -fr product
    cp -r SS_ILProduct product
 #   chmod +x ./product/build/workroundforilgit
 #   ./product/build/workroundforilgit $WORKSPACE/rnc
    ############  finish workround  ##################
}


get_dependency_list(){
   #######  get depenency from dashboard db #########
   
    gs="https://$GERRIT_SERVER"
    module=$SUBSYSTEM
  	host="hzdatav01.china.nsn-net.net" 
  	db="ilcidashboard"
  	
  	cmd="select Subsystem from il_ci_dashboard_group  where GroupName != 0 and Subsystem <> '$module' and GroupName=(select GroupName from il_ci_dashboard_group where Subsystem='$module')"
    depends=$(ssh eclipse@eclipseupd.china.nsn-net.net "mysql -uroot -pILMAN@db -hhzdatav01.china.nsn-net.net ilcidashboard -s -e \"$cmd\""|grep -v "Subsystem")

    for i in $(echo "$depends");do
        brc=$DEVBRANCH
        git archive --format=tar.gz  --remote=$gitrepo $CONFIG_BRANCH ${common_configle} |tar -xzO -f - |grep $i && brc=${COMMONBRANCH}
    	echo "$i $brc" >> $dependtext
    done
    ######### if code still in gerrit develop branch, try to phase the depenency ########
    
    if ! ${IS_MERGED};then 
	    deps=$(git --git-dir=./$module/.git log -1|grep "\[DEPENDS:.*\]"|sed "s/T[0-9]\+//g"|grep -Eo "[0-9]+")
	    if test -n "$deps";then
          for dep in $deps;do
            echo "[info] download DEPENDS: $dep"
                  gerritapi="${gs}/changes/${dep}?o=CURRENT_REVISION" 
                  echo "[info] curl -s $gerritapi"
                  rst=$(curl -sk $gerritapi)

                  sub_refs=$(echo "$rst"| grep "ref" |  head -1 | sed 's#.*: "\(.*\)".*#\1#')
                  module=$(echo "$rst"|grep '"project": '|  head -1 | sed 's#.*: ".*/\(.*\)".*#\1#')
                  echo "[info] echo ${module} ${sub_refs} >> $dependtext"
                  echo "${module} ${sub_refs}" >> $dependtext
          done
	    fi
	 fi
   echo "[info] cat $dependtext"
   cat $dependtext
}

switch_depenency_version(){

   	######### add rev into rev.txt #################
   	gitver=$(git --git-dir=$SUBSYSTEM/.git --work-tree=$SUBSYSTEM log -1|grep ^commit|cut -d" " -f2)
   	version=$(git --git-dir=$SUBSYSTEM/.git --work-tree=$SUBSYSTEM rev-list --all|wc -l)
    echo "$SUBSYSTEM branches/$REFS r$version $gitver" > $revtext
    #########
   
    echo "[info]: switch dependency module to related branch"
   	while read item;do
       module=$(echo $item|awk '{print $1}')
       ref=$(echo $item|awk '{print $2}')
       echo "switch_depenency $module to $ref"
       git --git-dir=$module/.git --work-tree=./$module fetch -q origin $ref
       git --git-dir=$module/.git --work-tree=./$module reset --hard
       git --git-dir=$module/.git --work-tree=./$module checkout FETCH_HEAD
       
       ######### add rev into rev.txt #################
       gitver=$(git --git-dir=$module/.git --work-tree=$module log -1|grep ^commit|cut -d" " -f2)
       version=$(git --git-dir=$module/.git --work-tree=$module rev-list --all|wc -l)
       echo "$module branches/$ref r$version $gitver" >> $revtext
       #########
   	done < $dependtext
   	
}


workroundroundforcloudil(){
	  
	  imageserver="10.68.165.226"
	  echo "[info] ready to scp yaml file to ${imageserver} server"
	  if cat $revtext |grep "\(SS_ILTestDeployment\)\|\(SS_ILDeployment\)";then 
	    echo "[info] upload yaml and env from SS_ILTestDeployment"
	    echo "[info] get yaml from testdeployment to ${imageserver} server" 
	    ssh root@${imageserver} "mkdir -p /data/www-root/cloudil/$SUBSYSTEM/images/yaml"
	    
	    pushd SS_ILTestDeployment/new_yaml/IL_vRNC_specific
	    tar czvf cloudil-heat-templates.tgz  IL_vRNC.yaml IL_vRNC.env read.me modules/
	    scp ./cloudil-heat-templates.tgz root@${imageserver}:/data/www-root/cloudil/$SUBSYSTEM/images/yaml/
	    rm -f cloudil-heat-templates.tgz
	    popd
	  else
	    ###### when compile other subsystem scp yaml file from basepackage server to imageserver
      triggerfile="https://gitlabe1.ext.net.nokia.com/ILCI/trigger/raw/master/cloudil/latest_ok_smoke_tested/cloudil_smk_ok_trigger.txt"
      curl -k -s $triggerfile  -o trigger_file_txt
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
	
	    echo "[cmd] ssh root@${imageserver} \"mkdir -p /data/www-root/cloudil/$SUBSYSTEM/images/yaml\""
	    ssh root@${imageserver} "mkdir -p /data/www-root/cloudil/$SUBSYSTEM/images/yaml; \
	    cd /data/www-root/cloudil/$subsystem/images/yaml;rm -f *.yaml *.tgz *.txt"
	    echo "upload yaml file "
	    scp ./cloudil-heat-templates.tgz root@${imageserver}:/data/www-root/cloudil/$SUBSYSTEM/images/yaml/
	  fi

}


compile(){
   	cmd=$1
   	dependency=$(cat ${dependtext}|awk '{print $1}'|sort -u)
   
    if ${IS_MERGED} && [ "$PRODUCT" = "cloudil" ];then
   		workroundroundforcloudil
   	fi 
     
   	echo "[info] start running compile !"
   	echo "[cmd] $cmd $value -j \"$ciscript/submake.sh $SUBSYSTEM $(echo $dependency)\" > $LOGPATH/$compilelog"
   	$cmd $value -j "$ciscript/submake.sh $SUBSYSTEM $(echo $dependency)" > $LOGPATH/$compilelog 2>&1
   	EXITCODE=$?
}


runut(){
   	cmd=$1
   	echo "[info] start running ut !"
   	echo "[cmd] $cmd $value -j \"$ciscript/subut.sh $SUBSYSTEM ${coverage_log}\" > $LOGPATH/$utlog"
   	$cmd $value -j "$ciscript/subut.sh $SUBSYSTEM ${coverage_log}" > $LOGPATH/$utlog 2>&1
   
    export VARENT="test-x86"
   	cd $STATIC_SCRIPT_ROOT
   	./il_static_check.sh $PRODUCT  $SUBSYSTEM $WORKSPACE $LOGPATH/statistics
 	  EXITCODE=$? 
  	cd $WORKSPACE
}

runstatic(){
   	cd ${STATIC_SCRIPT_ROOT}
   	export PATH=$PATH:/apps/klocwork/bin
  	export VARENT="static-analysis"   #redefine the var as it is used in static check for both cloudil and il
  	echo "[cmd] ./il_static_check.sh $PRODUCT $SUBSYSTEM $WORKSPACE $LOGPATH/statistics"
   	./il_static_check.sh $PRODUCT $SUBSYSTEM $WORKSPACE $LOGPATH/statistics
   	EXITCODE=$?
   	cd $WORKSPACE
}

run(){
   	cmd="product/build/svnenv.sh"
   	if [ "$task" = "compile" ];then
   		compile $cmd 
   	elif [ "$task" = "ut" ];then
   		runut $cmd 
   	else
   		runstatic
   	fi
}

check_result(){

   if [ "$task" = "compile" ];then
      test -f $LOGPATH/$compilelog ||(echo "$LOGPATH/$compilelog not found";exit 1)
   	  cat $LOGPATH/$compilelog |grep ": \*\*\*" && exit 1
   elif [ "$task" = "ut"  ];then
      test -f $LOGPATH/$utlog ||(echo "$LOGPATH/$utlog not found";exit 1)
      cat $LOGPATH/$utlog |grep ": \*\*\*" && exit 1
      test -f ${ut_log} && (cat ${ut_log}|grep -E \(errors=.[1-9]+\)\|\(failures=.[1-9]+\) && exit 1)
   fi
   exit ${EXITCODE} 
}

collectlogs(){

   echo "[info] start to collect logs"
   dependency=$(cat ${dependtext}|awk '{print $1}')
   if [ "$task" = "compile" ];then
   	   for module in $(echo $SUBSYSTEM $dependency);do
   		  cp -r $WORKSPACE/$module/build/*.rpm  $LOGPATH/
 	   done
   elif [ "$task" = "ut" ];then
   	   test -e ${ut_log} && cp -f ${ut_log} $LOGPATH/
  	   test -e  $SUBSYSTEM/$coverage_log && cp -f  $SUBSYSTEM/${coverage_log} $LOGPATH/
   fi
   echo "[info]:collect logs finished!"
}
#####################   main execute  #################################
checkenv
checkout_inittial_code
get_dependency_list
switch_depenency_version
run
collectlogs
check_result


