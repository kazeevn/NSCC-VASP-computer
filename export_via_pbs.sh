#!/bin/bash
#PBS -l select=1:ncpus=1:mem=64gb:mpiprocs=1:ompthreads=1
#PBS -l walltime=00:30:00
#PBS -P 12003663
#PBS -q normal
#PBS -m n
#PBS -M kna@nus.edu.sg

module load miniforge3
conda activate vasp_computer
PROJECT_ROOT="/home/users/nus/kna/NSCC-VASP-computer/"
cd $PROJECT_ROOT
python export_run_data.py ${RUN_NAME}