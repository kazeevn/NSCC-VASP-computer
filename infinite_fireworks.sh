#!/bin/bash
PROJECT_ROOT="$1"
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "Error: PROJECT_ROOT must be provided as the first argument and be a directory (got: '$PROJECT_ROOT')" >&2
    exit 1
fi

source $PROJECT_ROOT/.env

# Set wait time between retries (in seconds)
WAIT_TIME=5
# $FIREWORKS_DIR is exported via .env
LAUNCH_DIR="$FIREWORKS_DIR/launch_dir"
LOG_DIR="$FIREWORKS_DIR/logdir"
mkdir -p "$LAUNCH_DIR"
mkdir -p "$LOG_DIR"
while true; do
    qlaunch --launch_dir "$LAUNCH_DIR" --logdir "$LOG_DIR" -r rapidfire
    echo "Exit code: $?. Retrying in $WAIT_TIME seconds..."
    sleep $WAIT_TIME
done
