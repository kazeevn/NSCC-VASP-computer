#!/bin/bash
#PBS -l select=1:ncpus=64:mem=128gb:mpiprocs=64:ompthreads=1
#PBS -l walltime=23:59:58
#PBS -P 12003663
#PBS -q normal
#PBS -m n
#PBS -M kna@nus.edu.sg
cd $PBS_O_WORKDIR

module swap PrgEnv-cray PrgEnv-intel
module swap intel intel/2022.0.2
module load mkl/2022.0.2
module load miniforge3
conda activate vasp_computer

SOCKET="/tmp/$(uuidgen).sock"
ssh -fN -oControlMaster=auto -oControlPath=/tmp/$(uuidgen).sock -oControlPersist=yes \
    -oServerAliveInterval=60 -oExitOnForwardFailure=yes \
    -L $SOCKET:localhost:17017 asp2a-login-nus02 &
export JOBFLOW_JOB_STORE__DOCS_STORE__PORT=""
export JOBFLOW_JOB_STORE__DOCS_STORE__HOST="$SOCKET"
echo "Started SSH forwarding via $SOCKET"
sleep 1

# Example:
# STRUCTURES="/home/users/nus/kna/NSCC-VASP-computer/mp_20_test.csv.gz"
# STRUCTURE_ID="mp-1660"
# PROJECT_ROOT="/home/users/nus/kna/NSCC-VASP-computer/"
# SCRATCH_ROOT=/home/users/nus/kna/scratch/dft_runs
JOBFLOW_FOLDER="$SCRATCH_ROOT/$RUN_NAME/jobflow/"
mkdir -p "$JOBFLOW_FOLDER"
python $PROJECT_ROOT/mongo_ping.py
python $PROJECT_ROOT/worker_local.py $STRUCTURES --structure-id $STRUCTURE_ID --job-folder "$JOBFLOW_FOLDER" --run-name "$RUN_NAME"
rm "$SOCKET"