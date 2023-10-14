#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include <cassert>
#include <cstdint>
#include <llvm-15/llvm/Analysis/LoopPass.h>
#include <llvm-15/llvm/IR/Constants.h>
#include <llvm-15/llvm/IR/DerivedTypes.h>
#include <llvm-15/llvm/IR/InstrTypes.h>
#include <llvm-15/llvm/IR/Operator.h>
#include <llvm-15/llvm/IR/PassManager.h>
#include <llvm-15/llvm/Support/MathExtras.h>
#include <llvm-15/llvm/Support/raw_ostream.h>
#include <memory>

using namespace llvm;

// References:
// * Hsu, 2021
// * llvm.org/docs/WritingAnLLVMPass.html
namespace {

struct LoopUnswitchPass : public LoopPass {
  // Strength reduction patterns
  static char ID;
  LoopUnswitchPass() : LoopPass(ID) {}

  virtual bool runOnLoop(Loop *L, LPPassManager &LPM) { return false; }
  virtual bool doInitialization(Loop *L, LPPassManager &LPM) { return false; }
  virtual bool doFinalization() { return false; }
};

} // namespace
char LoopUnswitchPass::ID = 0;
static RegisterPass<LoopUnswitchPass> P("loop-unswitch", "Loop Unswitch Pass",
                                        false /* Only looks at CFG */,
                                        false /* Analysis Pass */);