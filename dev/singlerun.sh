#!/bin/bash
task=$1
cd $task
cp ../{ase_relax.py,vasp_settings.py} .

echo "[`date`] Info: starting structure relaxation calculations ..."
python ase_relax.py  $task > ${task}_${PBS_JOBNAME}_${PBS_JOBID}_ase_vasp.log 2>&1
echo "[`date`] Info: Done."

cd ../