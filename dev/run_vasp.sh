#!/bin/bash
#PBS -N vasp
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
VASP_PATH="/home/users/nus/kna/wt_vasp/vasp.5.4.4/bin/"
export PATH=${VASP_PATH}:$PATH
export VASP_PP_PATH="/home/users/nus/kna/wt_vasp"
cd $VASP_RUN_DIR
mpirun -np 64 vasp_std