#!/bin/bash
#PBS -l select=1:ncpus=1:mem=64gb:mpiprocs=1:ompthreads=1
#PBS -l walltime=00:30:00
#PBS -P 11001786
#PBS -q normal
#PBS -m n

PROJECT_ROOT=/home/project/11001786/Crys-JEPA-VASP
source $PROJECT_ROOT/local_env.sh
cd $PBS_O_WORKDIR
EXTRA_ARGS=()
if [ -n "${RUN_NAMES}" ]; then
    EXTRA_ARGS+=(--run-names ${RUN_NAMES})
fi
if [ -n "${ATOMATE_JOB_NAME}" ]; then
    EXTRA_ARGS+=(--atomate-job-name "${ATOMATE_JOB_NAME}")
fi
python $PROJECT_ROOT/export_run_data.py "${EXTRA_ARGS[@]}"

