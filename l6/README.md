# Discussion

* __Summary__
  * [To From SSA](https://github.com/matth2k/cs6120-exercises/blob/main/l6/)
    * Source Files
      * `to_ssay.py` and `from_ssa.py` The main driver code for transforming a program to and from
      * `butils` Directory for my utility code
        * `butils/cfg.py` An API to build control flow graphs from programs. Has a `Block` api as well.
        * `butils/ssa.py` Takes in a CFG and returns a CFG is SSA form.
        * `butils/dominance.py` The generic dominance info framework

* __Implementation Details__
  * Overall, my SSA implementation follows the pseudo-code fairly closely. I construction the control-flow graph, gather dominance info, then kick off the SSA renaming.
  * I used GitHub Copilot for some boilerplate code, and I used the baseline implementation of SSA in the Bril repo to help debug some bugs when going roundtrip.
  * To manage the phi nodes, I subclassed my `Block` class into an `SSABlock`
    * `def update_phi_dest(self, var: str, type: Any, ssa_name: str = None)` creates or updates a phi node for variable `var` with the assignment `ssa_name`
    * `def update_phi_arg(self, var: str, label: str, ssa_name: str, insert=True)` adds or updates an argument to a phi node for block `label` with the name `ssa_name`.
    * `def insert_explicit_jmp(self, successors)` inserts a `jmp` operation at the block when the control-flow falls through the block.
    * `def pop_phi_nodes(self)` deletes the phi nodes and gives an iterator to the deleted nodes

* __Evaluation__
  * I evaluated my to and from SSA routine by running every benchmark on it. First, I shot for functional testing, then I also tested that it is indeed in SSA form with the `is_ssa.py` script.
    * In the "to" direction, I can handle every single bril program in the repo, both in functionality and actually meeting SSA form.
    * In the "from" direction, I can handle all but a handful of the 120 programs. However, there is no program that I fail on that the baseline implementation provided in `examples/from_ssa.py` doesn't also fail on. In fact, I'm happy that my solution fails on less than the baseline.
      * I experimented with forcing variables to be initialized with some success, but I don't really know what implications this has for correctness. So I dropped it. What's the right thing to do here? Maybe having an `undef`?


* __Anything Hard or Interesting?__
  * This was the hardest task so far, with many pitfalls:
    * My stack was held as a `dict[list[Block]]`, but I was not popping it correctly because all the dictionaries had the same references to the underlying lists. I needed to `deepcopy` the variable or else I would still have the unpopped stack.
    * Some control flow graphs have unreachable blocks if you parse them naively, like having unreachable jumps or return instructions, and this interfered with my algorithm I modified my `CFG` class to sniff out these unreachable blocks and just drop them.
    * My SSA code failed on cases where the entry block contains a phi node, because the start the program has no previous block to switch on. In this case, if the entry block has a back edge I reanchor the control-flow graph with a new dummy entry block.
    * When I first implemented control-flow graphs I bundled consecutive labels into one basic block. I didn't like having so many blocks that have zero instructions in them. However, this decision hurt me when implementing SSA. I ended up with two alternative workarounds for this:
      * Just change the block formation step to no longer bundle consecutive labels together
      * Insert jump instructions between every consecutive label, where the jump takes you to the "real" block. Like so:
        ```
          .endif.139:
          jmp .endif.31;
          .endif.132:
          jmp .endif.31;
          .endif.125:
          jmp .endif.31;
          .endif.118:
          jmp .endif.31;
          .endif.111:
          jmp .endif.31;
          .endif.104:
          jmp .endif.31;
          .endif.97:
          jmp .endif.31;
          .endif.31:
        ```
    * Finally, it took me the longest time to realize that I needed a separate `varCounter` dictionary separate from the stack. Otherwise, we won't pull a fresh variable name when branching in the dominator tree. This to me was the detail missing the most from the pseudo code.