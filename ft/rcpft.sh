#!/bin/bash

SCRIPT_DIR=$(dirname $(readlink -f $0))
WORK_DIR=$(pwd)
GERRIT_SERVER="hzslgerrit.int.net.nokia.com:8282" # "gerrite1.ext.net.nokia.com:8282"

PRODUCT=$1
TASK_NAME="${2}_${BUILD_NUMBER:-0}"
SUBSYSTEM=$3
IMAGE_URL=http://10.68.165.226/cloudil/$SUBSYSTEM/images
#IMAGE_URL=http://10.56.118.71/CloudIL/vrnc/ci/latest/images
DEVICE_POOL=${DEVICE_POOL:-commonilft}
CTAAS_SERVER=${CTAAS_SERVER:-http://ctaas.dynamic.nsn-net.net}
TASK_CREATE_URL="${CTAAS_SERVER}/coci/cloud/add_task_for_fc"
TASK_STATUS_URL="${CTAAS_SERVER}/coci/cloud/get_task_status"
TASK_QUERY_URL="${CTAAS_SERVER}/coci/cloud/search_task"
TASK_LIST=()
TASK_OUTPUT_XML=()

help()
{
  echo "usage: rcpft.sh <product> <image name> <subsystem name>"
  echo "  -y  yaml template url for special"
  echo "  -h  helper"
}

while getopts "y:h" arg
do
   case $arg in
        y)
          yaml_url=$OPTARG
          ;;
        h)help
          exit 0
          ;;
        ?)
          echo "unkonw argument"
          exit 1
          ;;
   esac
done

# Not used since ctaas prepare the test env
function prepare_test_env(){
    cloudtaf_branch_refs=$1
    rcpci_branch_refs=$2
    rm -rf cloudtaf rcpci
    
    if [ -z $GERRIT_SERVER ];then  
        GERRIT_SERVER="hzslgerrit.int.net.nokia.com:8282"
    fi
    git clone ssh://hzci@$GERRIT_SERVER/scm_rcp/cloudtaf
    git --git-dir=cloudtaf/.git --work-tree=${WORK_DIR}/cloudtaf fetch origin ${cloudtaf_branch_refs}
    git --git-dir=cloudtaf/.git --work-tree=${WORK_DIR}/cloudtaf checkout FETCH_HEAD
    
    git clone ssh://hzci@$GERRIT_SERVER/scm_rcp/rcpci
    git --git-dir=rcpci/.git --work-tree=${WORK_DIR}/rcpci fetch origin ${rcpci_branch_refs}
    git --git-dir=rcpci/.git --work-tree=${WORK_DIR}/rcpci checkout FETCH_HEAD
}

function prepare_test_cases(){
    CASELIST=""
    EXCLUDE_TAGS="--exclude not-*"
    
    for i in `cat $SCRIPT_DIR/rcp_cci_case.config|grep ${SUBSYSTEM}:|cut -d ":" -f2`;do
      testcase=`echo $i|sed s#.*testcases/##g|grep  -oE ".*/[a-z_A-Z0-9]+"|tr "/" "."`
      CASELIST="$CASELIST -s $testcase"
    done
    
    if test "$CASELIST";then
        case $PRODUCT in
            vRNC)
                INCLUDE_TAGS="--include phase-CCIORphase-FastCIANDproduct-vRNC" 
                CASELIST="`echo $CASELIST` testcases/CloudIL"
                ;;
            ilvrnc)
                INCLUDE_TAGS="--include phase-FastCIANDproduct-vRNC"
                CASELIST="`echo $CASELIST` testcases/rcp"
                ;;
             *) echo "Not found: $PRODUCT";;
        esac
    else
        CASELIST="-s example.examples testcases/example"
    fi
}

function prepare_image_info(){
    # vRNC
    # CI_DEPLOYER_IMAGE_URL, CI_DEPLOYER_IMAGE_NAME
    # image_name=`wget -q -O - http://10.68.165.226/cloudil/$SUBSYSTEM/images/ | grep -o ">CIU_vRNC_rcp-ci.*.qcow2" | sed 's/^.//'`
    # CI_DEPLOYER_IMAGE_PATTERN="-v CI_DEPLOYER_IMAGE_PATTERN:CIU.*[0-9].*.qcow2"
    YAML="{TPLZIP}#IL_vRNC.yaml"
    DEPLOYMENT="CloudIL"
    BUILD="$IMAGE_URL/CIU_vRNC_rcp-ci.*.qcow2"
    #BUILD="$IMAGE_URL/CLOUD_IL_RNC_18.12.0-ci_r11.*.qcow2"
}

function fetch_ctaas_log(){
    download_link=$1
    output_xml=output_$2.xml
    echo "Downloading $download_link to rcpci/rfcli_output"
    mkdir -p $WORK_DIR/rcpci/rfcli_output
    curl -m 600 --retry 2 -L -o $WORK_DIR/rcpci/rfcli_output/${output_xml} $download_link
    TASK_OUTPUT_XML=($output_xml ${TASK_OUTPUT_XML[@]})
    # unzip -o -d $WORK_DIR/rcpci/rfcli_output archive.zip
    # mv $WORK_DIR/rcpci/rfcli_output/logs/* $WORK_DIR/rcpci/rfcli_output/
    # rm -rf archive.zip $WORK_DIR/rcpci/rfcli_output/logs
}

function do_wordaround_extra_task(){
    echo "Do workaround for subsystem $SUBSYSTEM if needed"
    case $SUBSYSTEM in
        SS_ILEITP|SS_ILFaStDist)
            EXCLUDE_TAGS="--exclude not-ready"
            INCLUDE_TAGS="--include tt_performanceANDphase-CCI"
            CASELIST="-s CloudIL.TT.TR.Performance testcases/CloudIL"
            DEVICE_POOL="commonilTT"
            TASK_NAME="${TASK_NAME}_performance"
            create_ft_task
            ;;
         *) echo "no workaround needed"
            ;;
    esac
}

function create_ft_task(){
    # Before create ft task, define the following variables
    # TASK_NAME, DEVICE_POOL
    # EXCLUDE_TAGS, INCLUDE_TAGS, CASELIST
    # BUILD, YAML, DEPLOYMENT
    task_create_cmd="curl -s -F \"pool=${DEVICE_POOL}\" -F \"framework=taf\" \
                -F \"task_name=$TASK_NAME\" \
                -F \"lib_repo=scm_rcp/cloudtaf\" -F \"lib_branch=master\" \
                -F \"case_repo=scm_rcp/rcpci\" -F \"case_branch=master\" \
                -F \"case_list=${EXCLUDE_TAGS} ${INCLUDE_TAGS} ${CASELIST}\" \
                -F \"build=$BUILD\" -F \"yaml=$YAML\" -F \"deployment=${DEPLOYMENT}\" \
                -F \"priority=2500\" $TASK_CREATE_URL"
    
    echo "task create: $task_create_cmd"
    # create expected result {"status": "ok", "msg": "ok", "taskid": 123456}
    task_create_result=`eval $task_create_cmd`
    echo "task create result: $task_create_result"
    if [ "${task_create_result}" = "" ] ;then
            echo "[ERROR]create task failed, can not get respond from ctaas, please check if ctaas is available!"
            exit 1
    fi
    task_id=`echo "$task_create_result" | grep -Eo '[0-9]+'`
    TASK_LIST=(${task_id} ${TASK_LIST[@]})
}

function waiting_tasks_to_end(){
    end_status=("done" "error" "ignore" "timeout")
    echo "Wait until task end..."
    echo "Task list: ${TASK_LIST[@]}"
    echo "Task detail like <${CTAAS_SERVER}/coci/cloud/task_detail?task_id=${TASK_LIST}>"
    while ((${#TASK_LIST[@]}>0));do
        for task_id in ${TASK_LIST[@]}
        do
            task_status_cmd="curl -s -F \"id=$task_id\" $TASK_STATUS_URL"
            task_status_result=`eval $task_status_cmd`
            status=`echo ${task_status_result} | grep -Eo '"status": "[a-z]+"' | sed 's/.*: \"\([a-z]*\).*/\1/g'`
            if [[ "${end_status[@]}"  =~ "${status}" ]]; then
                # Waiting build done 
                # Since the logs will upload to server after task done
                build_url=`echo ${task_status_result} | grep -Eo '"build_url": "[^\"]+"'| sed 's/.*: \"\([^\"]*\).*/\1/g'`
                isbuilding=`curl -s ${build_url}api/json | grep -Eo '"building":(true|false)' | sed 's/"building":\(.*\)/\1/g'`
                if [ "${isbuilding}"x = "true"x ];then
                    echo "Build is still in running, waiting build to end after task done"
                    continue
                fi
                build_result=`curl -s ${build_url}api/json | grep -Eo '"result":[a-zA-Z"]+' | sed 's/"result":\(.*\)/\1/g'`
                echo "Task ${task_id}, the build result is ${build_result}"
                echo `echo ${task_status_result} | grep -Eo '"task_link": "[^,]+"'`
                echo `echo ${task_status_result} | grep -Eo '"build_url": "[^,]+"'`
                echo `echo ${task_status_result} | grep -Eo '"log_file": "[^,]+"' | sed 's/"log_file"/"log_link"/g'`
                echo `echo ${task_status_result} | grep -Eo '"case_count": "[^,]+"'`
                echo `echo ${task_status_result} | grep -Eo '"pass_count": "[^,]+"'`
                echo `echo ${task_status_result} | grep -Eo '"fail_count": "[^,]+"'`
                
                log_file=`echo ${task_status_result} | grep -Eo '"log_file": "[^,]+"'`
                output_xml=`echo $log_file | cut -d ":" -f 2- | tr -d '"' | sed "s/log.html$/output.xml/"`
                if [ -n "${output_xml}" ];then
                    fetch_ctaas_log $output_xml $task_id
                else
                    echo "ERROR: task ended as ${status}"
                    exit 1
                fi
                TASK_LIST=(${TASK_LIST[@]/${task_id}})
            fi
        done
        sleep 30
    done
    if (( ${#TASK_OUTPUT_XML[@]}>0 )); then
        cd $WORK_DIR/rcpci/rfcli_output && rebot --merge -o output.xml ${TASK_OUTPUT_XML[@]}
        [ "$?" -ne "0" ] || rm -rf ${TASK_OUTPUT_XML[@]}
    fi
}

prepare_test_cases
prepare_image_info
create_ft_task
do_wordaround_extra_task
waiting_tasks_to_end


