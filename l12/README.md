# Lesson 12 Discussion

* __Summary__
  * [Offline Speculative Execution](https://github.com/matth2k/cs6120-exercises/blob/main/l12)
    * `bril-br.ts` counts the number of speculative executions that complete versus are aborted.
    * `brili.ts` prints the trace fo a program as it is interpreted.
    * `findHotPath.py` analyzes the trace in a brute force way to find the hottest path in the CFG.
    * `insertTrace.py` takes in the hotpath of a program as arguments and carries out the program transform needed for speculative execution.
    * `workingExamples.sh` is a script that runs a selection of the Bril benchmarks and records the results relevant to speculative execution.

* __Implementation Details__
  * I used the reference `brili` interpreter written in TypeScript as a baseline. Then, I made two forks of it.
    * One fork is used for printing a program trace to terminal.
    * One is used to help me collect results: it prints out the number of commits and aborts observed during execution.
  * I wrote a helper program to analyze that trace: `findHotPath.py`.
    * This is probably the weakest part of my implementation. I start out with the hottest block in the program then iterate off of it until the path I am building gets too cold.
  * I have a compiler pass `insertTrace.py` that takes in this hot path as an input and transforms the Bril program.
    *

* __Evaluation__
  As long as we are using an interpreter, we will not be getting program speedups without chaining this pass into more optimizations. For instnace, unless we strengthen the guard statements, we don’t have the opportunity for common subexpression elimination. Hence, I don't have any real speedups to report in this assignment. The real measure of success for this lesson is to hope that the speculative programs are only slightly slower. The logic being that if our hot path is truly hot, we won’t need to abort often. Hence, the speculative program should be only a little bit slower than the baseline if we find a good trace.

  With that being said, we can observe how well my speculative execution performs by comparing the relative number of aborts to commits:

  | Benchmark         | Blocks in Trace | Instrs in Trace | Commits | Aborts | Baseline (Instrs) | Speculative (Instrs) |
  | ----------------- | --------------- | --------------- | ------- | ------ | ----------------  | -------------------- |
  | quadratic         | 3               | 338             | 2       | 4      | 785               | 881                  |
  | mod_inv           | 2               | 15              | 14      | 1      | 558               | 599                  |
  | loopfact          | 2               | 79              | 1       | 2      | 116               | 135                  |
  | fizz-buzz         | 2               | 28              | 100     | 1      | 3652              | 3937                 |
  | factors           | 2               | 10              | 7       | 1      | 72                | 90                   |
  | check-primes      | 3               | 826             | 3       | 244    | 8468              | 55135                |
  | birthday          | 2               | 407             | 1       | 2      | 484               | 497                  |
  | armstrong         | 2               | 15              | 3       | 3      | 133               | 154                  |
  | cordic            | 2               | 27              | 8       | 1      | 517               | 540                  |
  | n_root            | 2               | 17              | 20      | 20     | 733               | 793                  |
  | norm              | 2               | 9               | 20      | 0      | 733               | 793                  |
  | sqrt              | 5               | 231             | 1       | 3      | 322               | 418                  |

  The results are pretty diverse, we have some good results like `mod-inv` and `cordic`. While others like `check-primes` are clearly bad traces to optimize off of.

* __Anything Hard or Interesting?__
  * Overall, I think the difficulty in this assignment is chosing reasonable heuristics that are both (1) easy enough to program and (2) actually capture enough hot paths to optimize.
