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
  echo "Terminating start-team.py process..."
  kill  $start_team_pid
  exit 0
}

# Trap SIGTERM and SIGINT signals
trap cleanup SIGTERM SIGINT

python3 start_team.py --server-port $server_port --use-random-port --close-server &
start_team_pid=$!

# Wait for the background process to finish
wait $start_team_pid