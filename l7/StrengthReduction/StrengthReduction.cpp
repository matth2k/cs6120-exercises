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
#include <llvm-15/llvm/Support/MathExtras.h>
#include <llvm-15/llvm/Support/raw_ostream.h>

using namespace llvm;

// Page 240 of Hsu, 2021 helped me with this
namespace {

struct StrengthReductionPass : public PassInfoMixin<StrengthReductionPass> {
  // Strength reduction patterns

  void rewriteMul2Shl(BinaryOperator &mul) {
    auto lhs = dyn_cast<ConstantInt>(mul.getOperand(0));
    auto rhs = dyn_cast<ConstantInt>(mul.getOperand(1));
    if (!((lhs != nullptr && isPowerOf2_64(lhs->getValue().getZExtValue())) ||
          (rhs != nullptr && isPowerOf2_64(rhs->getValue().getZExtValue()))))
      return;
    auto shift_amt =
        (lhs != nullptr && isPowerOf2_64(lhs->getValue().getZExtValue()))
            ? Log2_64(lhs->getValue().getZExtValue())
            : Log2_64(rhs->getValue().getZExtValue());
    auto operand =
        (lhs != nullptr && isPowerOf2_64(lhs->getValue().getZExtValue()))
            ? mul.getOperand(1)
            : mul.getOperand(0);
    // Idk if I'm even handing signed and unsigned types right, just getting the
    // pass to work
    auto intType = mul.getType();
    IRBuilder<> builder(&mul);
    auto *shl =
        builder.CreateShl(operand, ConstantInt::get(intType, shift_amt));
    mul.replaceAllUsesWith(shl);
    mul.eraseFromParent();
  }

  PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
    SmallVector<BinaryOperator *> mul2Rewrite;
    llvm::errs() << "let's go\n";
    for (auto &F : M) {
      for (auto &BB : F.getBasicBlockList()) {
        for (auto &I : BB.getInstList()) {
          if (auto *mul = dyn_cast<MulOperator>(&I)) {
            mul2Rewrite.push_back(&cast<BinaryOperator>(I));
          }
        }
      }
    }

    for (auto &mul : mul2Rewrite)
      rewriteMul2Shl(*mul);
    llvm::errs() << "done\n";
    return PreservedAnalyses::all();
  };
};

} // namespace

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return {.APIVersion = LLVM_PLUGIN_API_VERSION,
          .PluginName = "Strength Reduction Pass for CS6120",
          .PluginVersion = "v0.1",
          .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level) {
                  MPM.addPass(StrengthReductionPass());
                });
          }};
}
