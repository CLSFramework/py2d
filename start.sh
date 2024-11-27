#!/bin/bash

python_env=.venv/bin/activate
source $python_env

# Set the options, all the options are passed as environment variables
options=$@

echo "Options: $options"

# Function to handle termination
cleanup() {
  echo "Terminating all start_agent.py processes..."
  sleep 2
  # kill $pid
  exit 0
}

# Trap SIGTERM and SIGINT signals
trap cleanup SIGTERM SIGINT

run_command="python3 start.py"

$run_command $options &
pid=$!

# Wait for the process to finish
wait $pid