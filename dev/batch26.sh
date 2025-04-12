#!/bin/bash
#PBS -N wt_vasp_crystalformer
#PBS -l select=1:ncpus=64:mem=440gb:mpiprocs=64:ompthreads=1
#PBS -l walltime=23:59:59
#PBS -P personal-kna
#PBS -j oe
#PBS -q normal
#PBS -m abe
#PBS -M kna@nus.edu.sg
cd $PBS_O_WORKDIR

#---------------------------- Enviroments ----------------------------#
module swap PrgEnv-cray PrgEnv-intel
module swap intel intel/2022.0.2
module load mkl/2022.0.2
module load miniforge3
module load parallel
module list

# Load python
source "/app/apps/miniforge3/23.10/etc/profile.d/conda.sh"
conda activate wt_vasp

# Load VASP
VASP_PATH="/home/users/nus/kna/wt_vasp/vasp.5.4.4/bin/"
export PATH=${VASP_PATH}:$PATH

NP=64
#---------------------------- Calculations ----------------------------#
export ASE_VASP_COMMAND="mpirun -np ${NP} vasp_std"
export VASP_PP_PATH="/home/users/nus/kna/wt_vasp"
source parallel.sh indices_in_batch${batch}.txt

#----------------------------------------------------------------------#

