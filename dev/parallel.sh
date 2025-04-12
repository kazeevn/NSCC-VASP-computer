#!/bin/bash

WallTimeHour=24
NumParallel=1
file_for_index=$1
# args_for_input_index=`awk '$1=$1' OFS=' ' RS='' ${file_for_index}`
args_for_input_index=`paste -s ${file_for_index} | sed 's/\t/ /g'`

#----------------------------- Functions ------------------------------#
now(){
  date '+%Y-%m-%d %H:%M:%S'
}

BeginTime=`now`

MoniterTime(){
  let WallTime=${WallTimeHour}*3600
  LeftTime=$WallTime
  until [ ${LeftTime} -lt 10 ];
  do
    CurrentTime=`now`
    Duration=`expr $(date +%s -d "$CurrentTime") - $(date +%s -d "$BeginTime")`
    echo "Info: Jobs run duration of time: $Duration (s) ..."
    let LeftTime=${WallTime}-${Duration}
    if [ "${LeftTime}" -lt 10 ];then
      echo "Info: WARNING Timeout, exit the job ..."
      echo "Info: WARNING code: 9999."
      kill -15 $$
      exit 9999
    else
      sleep 120
    fi
  done
}

ParalellRun(){
  parallel -j        $NumParallel \
           --load    100% \
           --joblog  "parallel_run_${PBS_JOBNAME}_${PBS_JOBID}.log" \
           --verbose \
           "echo ${PBS_JOBNAME} slot: {%}, sequence: {#}; source ./singlerun.sh {};" \
           ::: ${args_for_input_index}
}

#---------------------------- Calculations ----------------------------#
# Moniter the run time, and trap the singal of 15
trap "echo 'Info: Timeout, exiting ..'; exit 9999" 15
MoniterTime &
ParalellRun
#----------------------------------------------------------------------#
