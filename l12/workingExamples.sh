#!/bin/bash
BRIL_DIR=/home/matth2k/bril/benchmarks
BENCHES="float/cordic.bril float/n_root.bril float/norm.bril float/sqrt.bril"
declare -A ARGS
ARGS["float/cordic.bril"]="1.047"
ARGS["float/n_root.bril"]=" "
ARGS["float/norm.bril"]=" "
ARGS["float/sqrt.bril"]=" "

ACTION=./recompile.sh

for bench in ${BENCHES}; do
    echo "=================================="
    fullpath=$(realpath ${BRIL_DIR}/${bench})
    stem=$(basename ${fullpath} .bril)
    echo "Running ${stem}"
    echo "=================================="
    ${ACTION} ${fullpath} ${ARGS[${bench}]}
done