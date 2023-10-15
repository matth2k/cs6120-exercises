
source buildHelper.sh
clang -S -O1 -emit-llvm $1 -o $1.ll
opt -load-pass-plugin build/LoopUnswitch/LoopUnswitchPass.so -passes="loop(loop-unswitch)" $1.ll > $1.tmp
llvm-dis $1.tmp -o $1.ll.opt
rm $1.tmp