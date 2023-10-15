#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include <cassert>
#include <cstdint>
#include <llvm-15/llvm/IR/Constants.h>
#include <llvm-15/llvm/IR/DerivedTypes.h>
#include <llvm-15/llvm/IR/InstrTypes.h>
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

  PreservedAnalyses run(Loop &L, LoopAnalysisManager &LAM,
                        LoopStandardAnalysisResults &AR, LPMUpdater &U) {
    llvm::errs() << "loop name: \n";
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
                    llvm::errs() << "loop unswitching pass for loop\n";
                    LPM.addPass(LoopUnswitchPass());
                    return true;
                  }
                  return false;
                });
          }};
}
