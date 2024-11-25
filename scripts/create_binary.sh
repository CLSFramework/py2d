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

nuitka --standalone --onefile --output-dir=binary ../start.py

# remove build directory

rm -rf binary/start.build
rm -rf binary/start.dist
rm -rf binary/start.onefile-build

# copy start.sh to binary directory

cp ../start.sh binary/start.sh

# change start.sh to run binary instead of python and to use separate rpc server

sed -i 's/run_bin=false/run_bin=true/g' binary/start.sh
sed -i 's/separate_rpc_server=false/separate_rpc_server=true/g' binary/start.sh

# copy start to binary directory

cp start binary/start