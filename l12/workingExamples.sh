#!/bin/bash
BRIL_DIR=/home/matth2k/bril/benchmarks
BENCHES="float/cordic.bril"
declare -A ARGS
ARGS["float/cordic.bril"]="1.047"

for bench in ${BENCHES}; do
    echo "=================================="
    fullpath=$(realpath ${BRIL_DIR}/${bench})
    stem=$(basename ${fullpath} .bril)
    echo "Running ${stem}"
    echo "=================================="
    ./recompile.sh ${fullpath} ${ARGS[${bench}]}
done