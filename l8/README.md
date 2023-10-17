# Discussion

* __Summary__
  * [LICM in LLVM](https://github.com/matth2k/cs6120-exercises/blob/main/l8)

* __Implementation Details__
  * I implemented a pass that hoists loop-invariant code to the preheader of a loop while using the newish LLVM pass manager.
  * My pass does not detect all invariant memory operations. I do, however, use `AliasAnalysis` to hoist memory operations which are guaranteed to be alias free.
  * I call my pass with `opt` with the most bare bones pipeline required to utilize my LICM pass. My pass pipeline is `cgscc(inline),mem2reg,dse,function(loop(loop-unswitch))`. 
    * `inline` allows me to find loop-invariant function executions.
    * If I did not run the `mem2reg` pass, all the loop-invariant code was hidden behind memory operations.
    * `dse` (dead store elimination) improves the changes that my loop body will be alias-free.
  * You can see the rest of my tool flow in [optCode.sh](https://github.com/matth2k/cs6120-exercises/blob/main/l8/optCode.sh)

* __Evaluation__
  * Evaluating my LICM pass for performance was tricky, because nearly all simple applications are bound by memory operations which are not loop-invariant. Consequently, Amdahl's law would suggest that it is going to be hard for me to notice any speedups with only LICM. I wanted to try to implement loop unswitching as well to see more performance gains, but I did not have enough time.
  * I evaluated numerous micro-benchmarks (invariant func call, hello world loop, ...), but focused mainly on 5 large benchmarks ([bzip2](https://sourceware.org/bzip2/), [gcc 3.5](https://gcc.gnu.org/), [oggenc](https://www.rarewares.org/ogg-oggenc.php), [TSVC](https://dl.acm.org/doi/10.5555/62972.62987), [STMR](https://www.cs.toronto.edu/~frank/csc2501/Readings/R2_Porter/Porter-1980.pdf)).

  | Benchmark     | LICM Instructions Moved | Lines of LLVM | Testcase                     | Speedup |
  | ------------- | ----------------------- | ------------- | ---------------------------- | ------- |
  | bzip2         | 3502                    |  31,086       | Roundtrip de/compress video  | 1.0     |
  | gcc 3.5       | 26041                   |  19,252,451   | n/a                          | n/a     |
  | oggenc        | 3125                    |  65,081       | Compress wav file            | 1.0     |
  | TSVC          | 161                     |  20,336       | Check output hash is correct | 1.02     |
  | STMR          | 0                       |  1996         | Check output is correct      | 1.0     |
  | funcCall      | 9                       |  84           | Check output num is correct  | 1.0     |

  As you can see from the chart above, LICM does not give raw performance gains without tackling memory operations. Most of the benchmarks, the majority of moved instructions are `getelementptr`'s. I'm not sure how these GEPS are getting lowered, but they may not even create `add` instructions because x86 instructions have their own offset field. Hence, the only instructions saved on are things like `sub`, `add`, `sext`, and `mul`.

  The only benchmark I saw a statistically significant speedup on is TSVC ([Test Suite for Vectorizing Compilers](https://dl.acm.org/doi/10.5555/62972.62987)). This maybe? makes sense as hopefully these benchmarks are less memory heavy comparatively speaking. Here, I could see some `icmp` and `fcmp` operations being moved which was a good sign.

  Overall, this assignment is leaving me very confused, because I don't have good intuition on how some of these LLVM instructions are lowered to x86. I even made sure to use `-O0` on the LLVM static compiler. I don't know how I could be removing so many instructions and not seeing a clear speedup. My future work would be to look at more auto-vectorization testcases to look for more clues.

  LLVM Version:
  ```
  Ubuntu LLVM version 15.0.7
    Optimized build.
    Default target: x86_64-pc-linux-gnu
    Host CPU: alderlake
  ```


* __Anything Hard or Interesting?__
  * It was hard to use the new LLVM pass manager as most of the documentation online was for the old one. I spend a long time setting up the code to register my loop pass as hook into `PipelineParsing` using the `LoopPassManager`.
  * It was hard to find test cases to utilize LICM. I'm not sure I achieved my goal, but in any case [this page](https://people.csail.mit.edu/smcc/projects/single-file-programs/) was a really good resouce for finding large single-file programs.
  * I was looking into [MemorySSA](https://llvm.org/docs/MemorySSA.html) to find invariant memory instructions, but I was too limited on time. It looks like the people working on LLVM are trying to model the memory dependence analysis problem differently.

* __References Used__
  * [Hsu, 2021](https://github.com/PacktPublishing/LLVM-Techniques-Tips-and-Best-Practices-Clang-and-Middle-End-Libraries)
  * https://discourse.llvm.org/t/how-to-write-a-loop-pass-using-new-pass-manager/70240
  * https://people.csail.mit.edu/smcc/projects/single-file-programs/
  * https://llvm.org/doxygen/LoopInfo_8cpp_source.html