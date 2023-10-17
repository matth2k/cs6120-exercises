#!/bin/bash
set -e
# The clang flags are super important to testing the optimization in isolation
clang -S -O1 -Xclang -disable-llvm-passes -emit-llvm $1 -o $1.ll
opt -load-pass-plugin build/LoopUnswitch/LoopUnswitchPass.so -passes="cgscc(inline),mem2reg,dse,function(loop(loop-unswitch))" $1.ll > $1.tmp 2> $1.moved
cat $1.moved
echo "Number of instructions moved in $1:"
cat $1.moved | grep "moving" | wc -l
llvm-dis $1.tmp -o $1.ll.opt
llc -filetype=obj $1.ll.opt -o $1.o
clang -no-pie $1.o -o $1.out -lm
rm $1.tmp $1.o $1.moved
