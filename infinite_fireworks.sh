#!/bin/bash

# Set wait time between retries (in seconds)
WAIT_TIME=5
FIREWORKS_DIR="$HOME/scratch/fireworks"
mkdir -p $FIREWORKS_DIR
while true; do
    qlaunch -r rapidfire --launch_dir "$FIREWORKS_DIR/launch_dir" --logdir "$FIREWORKS_DIR/logdir"
    EXIT_CODE=$?
    echo "Error (Code: $EXIT_CODE). Retrying in $WAIT_TIME seconds..."
    sleep $WAIT_TIME
done
