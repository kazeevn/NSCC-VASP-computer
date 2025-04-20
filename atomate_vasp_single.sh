#!/bin/bash
#PBS -l walltime=23:59:58
#PBS -P 12003663
#PBS -q normal
#PBS -m n
#PBS -M kna@nus.edu.sg
cd $PBS_O_WORKDIR

# ASPIRE2A
# HPE Cray EX 2x AMD EPYC Millan 7713 providing total compute capacity of up to 10 PFlops, 512 GB memory and 128 cores per node.
# // 17.04.25 Increasing memory 128 -> 192 resulted in much longer queue time
# comment = Not Running: Insufficient amount of resource: node_pool

module swap PrgEnv-cray PrgEnv-intel
module swap intel intel/2022.0.2
module load mkl/2022.0.2
module load miniforge3
conda activate vasp_computer

MONGODB_PORTAL=asp2a-login-nus02
export SOCKET="$TMPDIR/mongodb.sock"
ssh -fN -oControlMaster=auto -oControlPath=$TMPDIR/cm-$MONGODB_PORTAL.sock -oControlPersist=yes \
    -oServerAliveInterval=60 -oExitOnForwardFailure=yes \
    -L $SOCKET:localhost:17017 $MONGODB_PORTAL &
echo "Started SSH forwarding via $SOCKET"
sleep 1

# Example:
# STRUCTURES="/home/users/nus/kna/NSCC-VASP-computer/mp_20_test.csv.gz"
# STRUCTURE_ID="mp-1660"
# PROJECT_ROOT="/home/users/nus/kna/NSCC-VASP-computer/"
# SCRATCH_ROOT=/home/users/nus/kna/scratch/dft_runs
JOBFLOW_FOLDER="$SCRATCH_ROOT/$RUN_NAME/jobflow/$PBS_JOBID"
mkdir -p "$JOBFLOW_FOLDER"
NEW_JOBFLOW_CONFIG_FILE="$TMPDIR/jobflow-config.yaml"
python $PROJECT_ROOT/write_jobflow_config.py $NEW_JOBFLOW_CONFIG_FILE
export JOBFLOW_CONFIG_FILE=$NEW_JOBFLOW_CONFIG_FILE
python $PROJECT_ROOT/mongo_ping.py
python $PROJECT_ROOT/worker_local.py $STRUCTURES --structure-id $STRUCTURE_ID --job-folder "$JOBFLOW_FOLDER" --run-name "$RUN_NAME"
rm "$SOCKET"
rm "$NEW_JOBFLOW_CONFIG_FILE"