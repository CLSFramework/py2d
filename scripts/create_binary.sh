#!/bin/bash


# show error if binary directory already exists

if [ -d "binary" ]; then
  echo "binary directory already exists. Please remove it before running this script."
  exit 1
fi

# create binary directory

mkdir binary

# copy scripts/proxy to binary directory

mkdir binary/scripts
cp -r proxy binary/scripts/proxy

# copy formations directory to binary directory

mkdir binary/src
cp -r ../src/formations binary/src/formations

# create binary

nuitka --standalone --onefile --output-dir=binary ../start_agent.py

# remove build directory

rm -rf binary/start_agent.build
rm -rf binary/start_agent.dist
rm -rf binary/start_agent.onefile-build

# copy start_agents.sh to binary directory

cp ../start_agents.sh binary/start_agents.sh

# change all `python3 start_agent.py`` to ./start_agent.bin in binary/start_agents.sh

sed -i 's/run_bin=false/run_bin=true/g' binary/start_agents.sh

# copy start to binary directory

cp start binary/start