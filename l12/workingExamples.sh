#!/bin/bash
BRIL_DIR=/home/matth2k/bril/benchmarks
BENCHES="core/quadratic.bril core/mod_inv.bril core/loopfact.bril core/fizz-buzz.bril core/factors.bril core/check-primes.bril core/birthday.bril core/armstrong.bril float/cordic.bril float/n_root.bril float/norm.bril float/sqrt.bril"
declare -A ARGS
ARGS["core/quadratic.bril"]="-5 8 21"
ARGS["core/mod_inv.bril"]="46 10007"
ARGS["core/loopfact.bril"]="8"
ARGS["core/fizz-buzz.bril"]="101"
ARGS["core/factors.bril"]="60"
ARGS["core/check-primes.bril"]="50"
ARGS["core/birthday.bril"]="23"
ARGS["core/armstrong.bril"]="407"
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