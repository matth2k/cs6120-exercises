

clang -S -emit-llvm $1 -o $1.ll
opt -enable-new-pm=0 -load build/LoopUnswitch/LoopUnswitchPass.so -loop-unswitch $1.ll > $1.tmp
llvm-dis $1.tmp -o $1.ll.opt
rm $1.tmp