#!/bin/bash
RUN_NAME="test_run_1"
RUN_ROOT="/home/users/nus/kna/scratch/dft_runs/$RUN_NAME"
PBS_ROOT="$RUN_ROOT/PBS"
mkdir -p "$PBS_ROOT"
cd $PBS_ROOT
qsub -v RUN_NAME=$RUN_NAME, RUN_ROOT=$RUN_ROOT /home/users/nus/kna/NSCC-VASP-computer/atomate_vasp_single.sh