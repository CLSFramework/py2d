#!/bin/bash

# active .venv
source .venv/bin/activate

server_port=6000

while [ $# -gt 0 ]
do
  case $1 in
    --server-port)
      server_port=$2
      shift
      ;;
    *)
      echo 1>&2
      echo "invalid option \"${1}\"." 1>&2
      echo 1>&2
      usage
      exit 1
      ;;
  esac
    shift 1
done

# Function to handle termination
cleanup() {
  echo "Terminating all start_agent.py processes..."
  for pid in "${pids[@]}"; do
    kill $pid
  done
  exit 0
}

# Trap SIGTERM and SIGINT signals
trap cleanup SIGTERM SIGINT

# Init log directory
log_dir="$(pwd)/logs/$(date +'%Y-%m-%d_%H-%M-%S')_$((RANDOM % 900000 + 100000))"
mkdir -p $log_dir

# Initialize an empty array to store PIDs
pids=()

# Run start_agent.py 11 times and store each PID in the array
python3 start_agent.py --server-port $server_port --use-random-port --close-server --goalie --log-dir $log_dir &
pids+=($!)

for i in {2..11}; do
  python3 start_agent.py --server-port $server_port --use-random-port --close-server --log-dir $log_dir &
  pids+=($!)
done

python3 start_agent.py --server-port $server_port --use-random-port --close-server --coach --log-dir $log_dir &
pids+=($!)

# Wait for all background processes to finish
for pid in "${pids[@]}"; do
  wait $pid
done