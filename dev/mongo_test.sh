#!/bin/bash
#!/bin/bash
#PBS -N mongo-test
#PBS -l select=1:ncpus=1:mem=1gb:mpiprocs=1:ompthreads=1
#PBS -l walltime=00:05:00
#PBS -P 12003663
#PBS -q dev
#PBS -m n
#PBS -M kna@nus.edu.sg
module load miniforge3
conda activate vasp_computer

cd $PBS_O_WORKDIR
PORT_SEARCH_START=17017           # Start of local port range to search
PORT_SEARCH_END=18000             # End of local port range to search
find_free_port() {
  local start_port=${1:-10000} # Default start port if not provided
  local end_port=${2:-65535}   # Default end port if not provided
  local port
  echo "Searching for an available TCP port between $start_port and $end_port..."  >&2
  for port in $(seq "$start_port" "$end_port"); do
    # Try to bind to the port using Python. This is a reliable way to check availability.
    # It attempts to create a socket and bind it to '0.0.0.0' (all interfaces) and the port.
    # If successful (exit code 0), the port is free. It closes the socket immediately.
    if python -c "import socket; s = socket.socket(); s.bind(('', $port)); s.close()" &>/dev/null; then
      echo "$port" # Output the found port number
      return 0     # Success
    fi
  done
  # If the loop finishes without finding a port
  echo "Error: Could not find a free port in the range $start_port-$end_port." >&2
  return 1 # Failure
}
LOCAL_PORT=$(find_free_port "$PORT_SEARCH_START" "$PORT_SEARCH_END")

# Check if the function succeeded in finding a port
if [ $? -ne 0 ] || [ -z "$LOCAL_PORT" ]; then
  echo "Error: Port finding failed. Exiting." >&2
  exit 1 # Exit if no port was found
fi
export MONGODB_PORT="$LOCAL_PORT"
echo "Found available port: $MONGODB_PORT. Exported as MONGODB_PORT."

ssh -fN -L $MONGODB_PORT:localhost:17017 asp2a-login-nus02 &
sleep 1

python mongo_test.py