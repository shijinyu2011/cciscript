#!/bin/bash
echo ${VARENT}
if [ "`echo $VARENT`" = "wr-clouldil" ];then command="rpm";else command="rpm_ft";fi

for i in $(echo $*);do
    if [ ${i} = "SS_ILDiagnostic" ];then
        make clean -C $i/build;make rpm_ft -C $i/build PRMJ=4 INGDEPS=true || exit 1;
    else
        make clean -C $i/build;make $command -C $i/build PRMJ=4 INGDEPS=true || exit 1;
    fi
done
