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
__Make sure no MongoDB instance is running.__ Start MongoDB on __the host specified in jobflow.yaml__ (by default, `asp2a-login-nus02`):
```bash
 module load singularity
 singularity run --bind $HOME/mongodb/data:/data/db mongo.sif --auth --bind_ip_all
```
## Submit the fireworks into the MongoDB
```python
python submit_fireworks.py <strucures-file> <run-name>
```

