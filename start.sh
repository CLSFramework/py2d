#!/bin/bash

python_env=.venv/bin/activate

server_host=127.0.0.1
server_port=6000
disable_log_file=false
run_bin=false
separate_rpc_server=false

while [ $# -gt 0 ]
do
  case $1 in
    --server-host)
      server_host=$2
      shift
      ;;
    --server-port)
      server_port=$2
      shift
      ;;
    --disable_log_file)
      disable_log_file=true
      ;;
    --run-bin)
      run_bin=true
      ;;
    --separate-rpc-server)
      separate_rpc_server=true
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

usage() {
  echo "Usage: $0 [--server-host <server_host>] [--server-port <server_port>] [--disable_log_file] [--run-bin]"
}

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

# Initialize an empty array to store PIDs
pids=()

# Set options
options="--server-host $server_host --server-port $server_port --use-random-port --close-server"
if [ $disable_log_file = false ]; then
  # Init log directory
  log_dir="$(pwd)/logs/$(date +'%Y-%m-%d_%H-%M-%S')_$((RANDOM % 900000 + 100000))"
  mkdir -p $log_dir
  options="$options --log-dir $log_dir"
else
  options="$options --disable-log-file"
fi

# Run start.py or start.bin
if [ $run_bin = true ]; then
  run_command="./start.bin"
else
  # active .venv
  source $python_env
  run_command="python3 start.py"
fi

if [ $separate_rpc_server = true ]; then
  # Run start_agent.py 11 times and store each PID in the array
  $run_command $options --goalie &
  pids+=($!)

  sleep 2

  for i in {2..11}; do
    $run_command $options --player &
    pids+=($!)
  done

  $run_command $options --coach &
  pids+=($!)
else
  $run_command $options &
  pids+=($!)
fi

# Wait for all background processes to finish
for pid in "${pids[@]}"; do
  wait $pid
done