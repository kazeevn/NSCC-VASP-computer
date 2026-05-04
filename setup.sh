#!/bin/bash
set -eo pipefail

PROJECT_NAME=Ziqiao-Crystal
SCRATCH=/scratch/users/nus/kna/$PROJECT_NAME
PROJECT_FOLDER=/home/users/nus/kna/$PROJECT_NAME
MONGO_HOST=asp2a-login-nus01
PBS_PROJECT=11001786
CONDA_ENV=vasp_computer_v3
MONGO_IMAGE=docker://mongodb/mongodb-community-server:8.0.21-ubi9

CALCULATOR_PWD=$(openssl rand -base64 24 | tr -dc '[:alnum:]')
PYROTECHNICIAN_PWD=$(openssl rand -base64 24 | tr -dc '[:alnum:]')

module load singularity

MONGO_DB_DIR=$PROJECT_FOLDER/mongo_db
MONGO_INSTANCE=mongo-setup
mkdir -p "$MONGO_DB_DIR"

echo "Starting MongoDB (no auth) on $MONGO_HOST..."
singularity instance start --bind "$MONGO_DB_DIR:/data/db" \
    "$MONGO_IMAGE" "$MONGO_INSTANCE"
trap 'singularity instance stop "$MONGO_INSTANCE" >/dev/null 2>&1 || true' EXIT

singularity exec "instance://$MONGO_INSTANCE" mongod \
    --bind_ip_all --fork --dbpath /data/db --logpath /data/db/mongod.log

echo "Creating MongoDB users..."
singularity exec "instance://$MONGO_INSTANCE" mongosh "mongodb://localhost:27017" --quiet <<EOF
db.getSiblingDB("jobflow").createUser({
  user: "calculator",
  pwd: "${CALCULATOR_PWD}",
  roles: [{ role: "readWrite", db: "jobflow" }]
});
db.getSiblingDB("fireworks").createUser({
  user: "pyrotechnician",
  pwd: "${PYROTECHNICIAN_PWD}",
  roles: [{ role: "readWrite", db: "fireworks" }]
});
EOF

echo "Stopping MongoDB..."
singularity exec "instance://$MONGO_INSTANCE" mongod --shutdown --dbpath /data/db
singularity instance stop "$MONGO_INSTANCE"
trap - EXIT

LOGDIR=$SCRATCH/fireworks_log
mkdir -p "$PROJECT_FOLDER" "$PROJECT_FOLDER/fw_config" "$LOGDIR"

echo "Writing $PROJECT_FOLDER/jobflow.yaml..."
cat > "$PROJECT_FOLDER/jobflow.yaml" <<EOF
JOB_STORE:
  docs_store:
    type: MongoStore
    database: jobflow
    host: ${MONGO_HOST}
    port: 27017
    username: calculator
    password: ${CALCULATOR_PWD}
    collection_name: outputs
EOF

echo "Writing $PROJECT_FOLDER/fw_config/..."
cat > "$PROJECT_FOLDER/fw_config/FW_config.yaml" <<EOF
CONFIG_FILE_DIR: ${PROJECT_FOLDER}/fw_config
QUEUE_UPDATE_INTERVAL: 1
EOF

cat > "$PROJECT_FOLDER/fw_config/my_fworker.yaml" <<'EOF'
name: my_fworker
category: ""
query: "{}"
EOF

cat > "$PROJECT_FOLDER/fw_config/my_launchpad.yaml" <<EOF
host: ${MONGO_HOST}
port: 27017
name: fireworks
username: pyrotechnician
password: ${PYROTECHNICIAN_PWD}
logdir: ${LOGDIR}
Istrm_lvl: DEBUG
user_indices: []
wf_user_indices: []
EOF

cat > "$PROJECT_FOLDER/fw_config/my_qadapter.yaml" <<EOF
_fw_name: CommonAdapter
_fw_q_type: PBS
_fw_template_file: ${PROJECT_FOLDER}/fw_config/pbs_template.txt
rocket_launch: rlaunch -w ${PROJECT_FOLDER}/fw_config/my_fworker.yaml -l ${PROJECT_FOLDER}/fw_config/my_launchpad.yaml singleshot
select: 1
ncpus: 64
mem: 128gb
mpiprocs: 64
ompthreads: 1
walltime: '23:59:58'
queue: normal
account: null
job_name: null
logdir: ${LOGDIR}/
pre_rocket: null
post_rocket: null
EOF

cat > "$PROJECT_FOLDER/fw_config/pbs_template.txt" <<EOF
#!/bin/bash

#PBS -l select=\$\${select}:ncpus=\$\${ncpus}:mem=\$\${mem}:mpiprocs=\$\${mpiprocs}:ompthreads=\$\${ompthreads}
#PBS -l walltime=\$\${walltime}
#PBS -q \$\${queue}
#PBS -A \$\${account}
#PBS -G \$\${group_name}
#PBS -N \$\${job_name}
#PBS -o FW_job.out
#PBS -e FW_job.error
#PBS -P ${PBS_PROJECT}

module swap PrgEnv-cray PrgEnv-intel
module swap intel intel/2022.0.2
module load mkl/2022.0.2
module load miniforge3
conda activate ${CONDA_ENV}

\$\${pre_rocket}
cd \$\${launch_dir}
\$\${rocket_launch}
\$\${post_rocket}
EOF

cat > "$PROJECT_FOLDER/.env" <<EOF
export JOBFLOW_CONFIG_FILE=${PROJECT_FOLDER}/jobflow.yaml
export FW_CONFIG_FILE=${PROJECT_FOLDER}/fw_config/FW_config.yaml
export FIREWORKS_DIR=${SCRATCH}
EOF

chmod 600 "$PROJECT_FOLDER/jobflow.yaml" "$PROJECT_FOLDER/fw_config/my_launchpad.yaml"

echo "Done. Start Mongo with --auth, then: source $PROJECT_FOLDER/.env"
