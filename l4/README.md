# Discussion

* __Summary__
  * [Dataflow Solver Framework](https://github.com/matth2k/cs6120-exercises/blob/main/l4/)
    * Source Files
      * `dfsolver.py` The main driver code
      * `butils` Directory for my utility code
        * `butils/cfg.py` An API to build control flow graphs from programs. Has a `Block` api as well.
        * `butils/dataflow.py` The generic dataflow solver framework.
* __Implementation Details__
  * I implemented a generic dataflow solver that can transfer fowards and backwards.
  * This was a good exercise, because it helped me build more robust infrastructure for building control flow graphs, mutating them, then writing them back out to Json. In the end I get a super clean top-level method:
  ```
  brilProgram = json.load(args.input)
  dataflow = ANALYSES[args.analysis]
  for func in brilProgram["functions"]:
      cfg = CFG(func)
      ins, outs = dataflow.solve(cfg)
  ```
  * I have 5 analyses that you can run:
    * `--analysis liveness` Live variable analysis
    * `--analysis reaching` Reaching definitions analysis
    * `--analysis defined` All possibly defined variables (really just a sanity check for the solver)
    * `--analysis constants` Constant propagation anaylsis
    * `--analysis initialized` Variables that are guaranteed to be initialized
    * `--anaylsis interval` Interval analysis (Missing some features, like propagating to booleans. It also isn't smart enough to understand if it will converge or not)

  * I had Github Copilot on, but only for some repeated boilerplate code.

* __Evaluation__
  * To test correctness of the generic solver, I tested that all the dataflow algorithm outputs make sense for the test cases in `bril/examples/test/df`.
  * I also ran on all the benchmarks in `/core/` and this helped show some bugs causing the algorithm not to converge. The issues were in `merge()` and `transfer()` and not the solver itself. I give details on one of the bugs in the next section.

* __Anything Hard or Interesting?__
  * Reaching definitions analysis is hard because you don't want just a set of variables, you want the actual complete definition for the variable. But once you get it right, its pretty satisfying because this analysis's output to me is the most insightful into what the program is doing.
  * Interval analysis is hard, because you will want to use the intervals of integers to help find the interval of bools as well. I just didn't do that part. Also, the algorithm does not take into account when control flow edges become impossible (for example knowing that `i < n` is a pre-condition to entering the body). So even with my current implemention sometimes interval anaylsis does not converge.
  * I use `copy()` very liberally to avoid unintended side-effects. I don't want my data structures to be mutable when I pass them in. And here I found that if a CFG node had a back-edge onto itself it would cause an infinite loop if the `merge()` function mutated its inputs! So when a block adds itself to the worklist and the input is wrongly mutated, it causes a re-triggering in the output, adding itself to the work list. And so on! It was hard to debug!
