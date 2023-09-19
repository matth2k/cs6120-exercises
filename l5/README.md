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
  * TODO
  * I had Github Copilot on, but only for some repeated boilerplate code.

* __Evaluation__
  * Created a verify function
  * Ran the verify function on all benchmarks in core

* __Anything Hard or Interesting?__
  * Reverse post-order
  * Efficient idominators
