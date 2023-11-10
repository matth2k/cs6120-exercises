# Lesson 12 Discussion

* __Summary__
  * [Offline Speculative Execution](https://github.com/matth2k/cs6120-exercises/blob/main/l12)
    * `bril-br.ts` counts the number of speculative executions that complete versus are aborted.
    * `brili.ts` prints the trace for a program as it is interpreted.
    * `findHotPath.py` analyzes the trace in a brute force way to find the hottest path in the CFG.
    * `insertTrace.py` takes in the hotpath of a function as arguments and carries out the program transform needed for speculative execution.
    * `workingExamples.sh` is a script that runs a selection of the Bril benchmarks and records the results relevant to speculative execution.

* __Implementation Details__
  * I used the reference `brili` interpreter written in TypeScript as a baseline. Then, I made two forks of it.
    * One fork is used for printing a program trace to terminal.
    * One is used to help me collect results after the fact. It prints out the number of commits and aborts observed during execution.
  * I wrote a helper program to analyze that trace: `findHotPath.py`.
    * This is probably the weakest part of my implementation. I greedily start out with the hottest block in the CFG then iterate off of it until the path I am building gets too cold.
  * I have a compiler pass `insertTrace.py` that takes in this hot path as an input and transforms the Bril program.
    * This is the most thoughtful part of my implementation. I think I nailed merging the blocks in a trace while preserving the correct control flow and also avoiding speculating on unsafe instructions like `ret`.
    * The merged block is inserted where the hot path begins. All predecessors of the hot path are redirected to the speculative block. The speculative block will abort to the header of the hot path, and the speculative block will commit and return to the successor of the hot path.
    * With this technique, I always had functionally correct benchmarks. The previous control-flow graph API I made in other assignments really sped up this part.

* __Evaluation__
  
  As long as we are using an interpreter, we will not be getting program speedups without using extra optimizations passes. For instance, unless we strengthen the guard statements, we don’t have the opportunity for common subexpression elimination. Hence, I don't have any real speedups to report in this assignment. The real measure of success for this lesson is to hope that the speculative programs are only slightly slower. The logic being that if our hot path is truly hot, we won’t need to abort often. Hence, the speculative program should be only a little bit slower than the baseline if we find a good trace.

  With that being said, we can observe how well my speculative execution performs by comparing the relative number of aborts to commits as well as counting the number of instruction lying in the speculative execution path:

  | Benchmark         | Blocks in Trace | Instrs in Trace | Commits | Aborts |
  | ----------------- | --------------- | --------------- | ------- | ------ |
  | quadratic         | 3               | 338             | 2       | 4      |
  | mod_inv           | 2               | 15              | 14      | 1      |
  | loopfact          | 2               | 79              | 1       | 2      |
  | fizz-buzz         | 2               | 28              | 100     | 1      |
  | factors           | 2               | 10              | 7       | 1      |
  | check-primes      | 3               | 826             | 3       | 244    |
  | birthday          | 2               | 407             | 1       | 2      |
  | armstrong         | 2               | 15              | 3       | 3      |
  | cordic            | 2               | 27              | 8       | 1      |
  | n_root            | 2               | 17              | 20      | 20     |
  | norm              | 2               | 9               | 20      | 0      |
  | sqrt              | 5               | 231             | 1       | 3      |

  The results are pretty diverse, we have some good results like `mod-inv` and `cordic`. While others like `check-primes` are clearly bad traces to optimize off of. The theoretical speedup of the program lies in the amount of instructions saved. With that intution, we can calculate a very rough approximate for max feasible speedup assuming that:

  * Every instruction takes the same amount of time to execute
  * The commit vs abort count I measured is representative of executions with different arguments
  * Aborts themselves have no overhead
  * The dynamic compilation time is not accounted into the cost

  Speedup = Baseline / (Baseline - Instruction in Trace * No. Commits) 

  | Benchmark         | Baseline (Instrs) | Speculative (Instrs) | Max Feasible Speedup |
  | ----------------- | ----------------  | -------------------- | -------------------  |
  | quadratic         | 785               | 881                  | 7.2x                 |
  | mod_inv           | 558               | 599                  | 1.6x                 |
  | loopfact          | 116               | 135                  | 1.5x                 |
  | fizz-buzz         | 3652              | 3937                 | 4.3x                 |
  | factors           | 72                | 90                   | 36x                  |
  | check-primes      | 8468              | 55135                | 1.4x                 |
  | birthday          | 484               | 497                  | 6.3x                 |
  | armstrong         | 133               | 154                  | 1.5x                 |
  | cordic            | 517               | 540                  | 1.7x                 |
  | n_root            | 733               | 793                  | 1.9x                 |
  | norm              | 505               | 545                  | 1.6x                 |
  | sqrt              | 322               | 418                  | 3.5x                 |

  These speedup measures are a little bit silly though, because the best speedups are on tiny programs where the overhead of dynamic compilation would be the majority of the cost anyways.

* __Anything Hard or Interesting?__
  * Overall, I think the difficulty in this assignment is chosing reasonable heuristics that are both (1) easy enough to program and (2) actually capture enough traces to optimize.
  * Finally, given these limitations it was hard to get enough measurements to make a conclusion about my implementation.
