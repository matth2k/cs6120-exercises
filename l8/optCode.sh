#!/bin/bash
set -e
source buildHelper.sh
# The clang flags are super important to testing the optimization in isolation
clang -S -O1 -Xclang -disable-llvm-passes -emit-llvm $1 -o $1.ll
opt -load-pass-plugin build/LoopUnswitch/LoopUnswitchPass.so -passes="cgscc(inline),mem2reg,function(loop(loop-unswitch))" $1.ll > $1.tmp
llvm-dis $1.tmp -o $1.ll.opt
llc -filetype=obj $1.ll.opt -o $1.o
clang -no-pie $1.o -o $1.out
rm $1.tmp $1.o
