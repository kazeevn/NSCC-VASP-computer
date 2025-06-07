# Set up
## Conda environemnt
```python
module load miniforge3
conda env create -f environment.yml
conda activate vasp_computer
```
## Set up VASP
Follow the pymatgen [instructions](https://pymatgen.org/installation.html) on POTCAR Setup. To ensure Materials Project compatibility, make sure you use the old `PBE`, not `PBE_52` or `PBE_54`.
## Configure atomate2 & jobflow
```bash
mkdir -p ~/atomate2/{config,logs}
cp *.yaml.example ~/atomate2/config
```
Edit the configuration files, they won't work out of the box! Then add them to your `~/.bash_profile`:
```bash
export ATOMATE2_CONFIG_FILE="$HOME/atomate2/config/atomate2.yaml"
export JOBFLOW_CONFIG_FILE="$HOME/atomate2/config/jobflow.yaml"
```
# Usage
## Start MongoDB
__Make sure no MongoDB instance is running.__ Start MongoDB on __the host specified in jobflow.yaml__ (by default, `asp2a-login-nus02`). In `tmux`:
```bash
 module load singularity
 singularity run --bind /data/projects/12003663/mongodb_data:/data/db /data/projects/12003663/mongo.sif --auth --bind_ip_all
```
Test that it's accessible:
```python
python mongo_ping.py
```

## Submit the fireworks into the MongoDB
A _firework_ is a term in Fireworks framework denoting a computational job prepared in MongoDB.
```python
python submit_fireworks.py <structures.csv> <run-name>
```

## Submit the jobs to PBS
```bash
bash infinite_fireworks.sh
```
The script is a workaround around the PBS max job limit.

## Analyze the results
Edit `export_via_pbs.sh` to fit your environment, then
```bash
qsub -v "ATOMATE_JOB_NAME=MP GGA static, RUN_NAME=<run-name>" export_via_pbs.sh
```