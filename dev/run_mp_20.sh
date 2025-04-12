 for folder in mp_20_test/*; do 
    qsub -v VASP_RUN_DIR=$folder run_vasp.sh
 done