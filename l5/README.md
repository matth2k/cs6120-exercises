# Discussion

* __Summary__
  * [Dominance Info Framework](https://github.com/matth2k/cs6120-exercises/blob/main/l5/)
    * Source Files
      * `dminfo.py` The main driver code that prints the dominance tree
      * `butils` Directory for my utility code
        * `butils/cfg.py` An API to build control flow graphs from programs. Has a `Block` api as well.
        * `butils/dataflow.py` The generic dataflow solver framework.
        * `butils/dominance.py` The generic dominance info framework

* __Implementation Details__
  * Finding the dominators of each node is quite similar to the dataflow framework we created. I did not reuse the dataflow solver, but you probably could. I wanted to reorder the initial worklist to get convergence in less iterations, but I was having trouble getting the reverse post-order correct with cycles in the DFG.
  * I used GitHub Copilot for some boilerplate code, and I read some other online resources on dominators.
  * One you run the dominance framework on a CFG, I provide the following API
    * `def dominates(self, a: Block, i: Block) -> bool` returns true if `a` dominates `b`
    * `def strictly_dominates(self, a: Block, i: Block) -> bool` returns true if `a` dominates `b` and `a != b`
    * `def immediately_dominates(self, a: Block, i: Block) -> bool` returns true if `a` is an immediate dominator of `b`
    * `def get_dom_tree(self) -> dict[str, set]` returns the dominator tree as map from block name to a set of blocks
    * `def get_dom_frontier(self) -> dict[str, set]` returns map from block name to a set of blocks on the dominance frontier

* __Evaluation__
  * As for evaluating the implementation of finding dominators, immediate dominators, and dominance tree I first ran my program on every `core` and `float` benchmark just as first pass for bugs.
  * Then, I implemented a `verify()` function to help test for correctness.
    * I use a DFS traversal to find every simple cyclic path in the CFG that starts from the entry block, storing the incremental path as the verticies $(v_1, v_2, ..., v_k)$. At each node visit $v_k$, I check that for all dominators of $v_k$ they are contained within the path (otherwise that would contradict it being a dominator). My rationale is that this approach would find all the false positive dominators. The false negatives are caught by reconstructing the dominators along all paths that end on node $v_k$.
    * Am I missing anything by terminating at simple cycles?
    * Assuming my `verify()` is watertight, I don't need to go any further to verify the dominator tree or dominance frontier, since I calculated those directly by definition without any shortcuts.


* __Anything Hard or Interesting?__
  * The fact that the CFG is not a DAG makes the formal verification as well as the run time optimization tricky.
  * When we move to SSA form, I want to try to reuse the dominance framework I've built up for finding dominators of individual operations.