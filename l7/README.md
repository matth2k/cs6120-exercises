# Discussion

* __Summary__
  * [Strength Reduction for Mul2Shl](https://github.com/matth2k/cs6120-exercises/blob/main/l7/StrengthReduction/StrengthReduction.cpp)

* __Implementation Details__
  * I implemented a pass that rewrites multiply instructions as logical shift lefts when one of the operands is constant and a power of 2. I used Chapter 10 of [Hsu, 2021](https://github.com/PacktPublishing/LLVM-Techniques-Tips-and-Best-Practices-Clang-and-Middle-End-Libraries) as a reference.

* __Evaluation__
  * I specifically did such a small scale optimization so that I could have more confidence that it is correct while using only a handful of tests. Since I wanted to rewrite multiplication by constant powers of 2, my main test case was just multiplying `argc`:
  ```c
  int main(int argc, char *argv[]) {
    return argc * 64U;
  }
  ```

  Here we can see the before an after of rewriting:
  Before:
  ```
  %7 = mul i32 %6, 64
  ret i32 %7
  ```
  After:
  ```
  %7 = shl i32 %6, 6
  ret i32 %7
  ```


* __Anything Hard or Interesting?__
  * I learned the difference between an `Operator`` and `Instruction`` in LLVM. Basically, an operator carries less meaning than an instruction. The class is just meant to capture the commonality between constant expressions and instructions in SSA.
  * I did not bother to implement a check to see if one of the operands are negative, so please don't use my pass in a real compiler.
  * How do I rewrite the pass using a pattern matching programming pattern? I couldn't easily find info on this. Is the pattern rewriter MLIR exclusive?