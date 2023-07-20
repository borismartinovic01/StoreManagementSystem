#!/bin/bash

file_path=$1

rm -rf ./solidity/output
docker run -v $(pwd)/solidity:/sources ethereum/solc:0.8.18 -o /sources/output --abi --bin /sources/"$file_path"