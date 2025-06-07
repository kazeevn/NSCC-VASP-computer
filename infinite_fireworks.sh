#!/bin/bash

# Set wait time between retries (in seconds)
WAIT_TIME=5
FIREWORKS_DIR="$HOME/scratch/fireworks"
LAUNCH_DIR="$FIREWORKS_DIR/launch_dir"
LOG_DIR="$FIREWORKS_DIR/logdir"
mkdir -p "$LAUNCH_DIR"
mkdir -p "$LOG_DIR"
while true; do
    qlaunch --launch_dir "$LAUNCH_DIR" --logdir "$LOG_DIR" -r rapidfire
    EXIT_CODE=$?
    echo "Error (Code: $EXIT_CODE). Retrying in $WAIT_TIME seconds..."
    sleep $WAIT_TIME
done
