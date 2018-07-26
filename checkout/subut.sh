#!/bin/bash
subsystem=$1
#if [ "`echo $label`" = "ILCCI" ];then
#   make utest -C $subsystem/build
#   cd $subsystem
#   python /home/hzscm/cci_tools/cci-script/gcovr -r ./ -R -x > $subsystem-coverage.xml
#else
  
make test -C $subsystem/build
#cd $subsystem
#python /home/hzscm/cci_tools/cci-script/gcovr -r ./ -R -x > $subsystem-coverage.xml
#fi
