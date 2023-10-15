#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include <cassert>
#include <cstdint>
#include <llvm-15/llvm/Analysis/ValueTracking.h>
#include <llvm-15/llvm/IR/Constants.h>
#include <llvm-15/llvm/IR/DerivedTypes.h>
#include <llvm-15/llvm/IR/InstrTypes.h>
#include <llvm-15/llvm/IR/Instruction.h>
#include <llvm-15/llvm/IR/Instructions.h>
#include <llvm-15/llvm/IR/Operator.h>
#include <llvm-15/llvm/IR/PassManager.h>
#include <llvm-15/llvm/Passes/OptimizationLevel.h>
#include <llvm-15/llvm/Support/MathExtras.h>
#include <llvm-15/llvm/Support/raw_ostream.h>
#include <llvm-15/llvm/Transforms/Scalar/LoopPassManager.h>

using namespace llvm;

// References:
// * Hsu, 2021
// * discourse.llvm.org/t/how-to-write-a-loop-pass-using-new-pass-manager/70240
namespace {

struct LoopUnswitchPass : public PassInfoMixin<LoopUnswitchPass> {

  // LoopInfo.cpp
  bool instIsInvariant(Loop &L, Value &V) {
    if (auto I = dyn_cast<Instruction>(&V))
      return !L.contains(I);
    return true;
  }

  PreservedAnalyses run(Loop &L, LoopAnalysisManager &LAM,
                        LoopStandardAnalysisResults &AR, LPMUpdater &U) {
    DenseSet<Instruction *> loopInvariant;
    if (!L.getLoopPreheader())
      return PreservedAnalyses::all();
    bool changing = true;
    while (changing) {
      changing = false;
      for (auto &BB : L.getBlocks()) {
        SmallVector<Instruction *> instToMove;
        for (auto &I : BB->getInstList()) {
          bool loopInvariant = !dyn_cast<BranchInst>(&I) &&
                               isSafeToSpeculativelyExecute(&I) &&
                               !I.mayReadOrWriteMemory();
          for (int i = 0; i < I.getNumOperands(); ++i) {
            if (!instIsInvariant(L, *I.getOperand(i))) {
              loopInvariant = false;
              break;
            }
          }
          if (loopInvariant)
            instToMove.push_back(&I);
        }
        for (auto I : instToMove) {
          changing = true;
          errs() << "moving instruction: " << *I << "\n";
          I->moveBefore(L.getLoopPreheader()->getTerminator());
        }
      }
    }
    return PreservedAnalyses::all();
  }
};

} // namespace

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return {.APIVersion = LLVM_PLUGIN_API_VERSION,
          .PluginName = "LoopUnswitchingPassCS6120",
          .PluginVersion = "v0.1",
          .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, LoopPassManager &LPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "loop-unswitch") {
                    LPM.addPass(LoopUnswitchPass());
                    return true;
                  }
                  return false;
                });
          }};
}
