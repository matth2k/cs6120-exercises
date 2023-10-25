# Discussion

* __Summary__
  * [Semi-space Garbage Collector in BRIL](https://github.com/matth2k/cs6120-exercises/blob/main/l9)

* __Implementation Details__
  * I used the reference `brili` interpreter written in TypeScript as a baseline.
  * Within the `Heap` class, I implemented a method called `doCollection()` that traces through the roots and the rest of the allocation graph. Allocations that are reachable from the roots are copied from the "from space" to the "to space".
  * I also needed to modify the `State` struct to contain a separate `roots` set, because each function has its own environment that can contain pointers. In my implementation, the roots of the current dynamic scope are the pointers in the current environment unioned with the roots of the callstack. I think using dynamic scoping to collect the roots is might be incorrect in some cases, but this approach worked for all the memory benchmarks for me.
  * I wrote a small utility called `removeFree.py`, that removes `free` instructions inside BRIL programs and replaces them with a dummy instruction that clobbers the pointer variable. This is an easy way to limit some memory leaks from dead variables hanging in the environment.
  * I used GitHub Copilot to help me with some of the TypeScript syntax that was unfamiliar to me.

* __Evaluation__
  * I evaluated my garbage collector by running it at different intervals with increasing frequency. To elaborate, I ran three scenarios:
    * Run the garbage collector when we run out of space in the "from space"
    * Run the garbage collector on every allocation
    * Run the garbage collector every single instruction

  * Using these three configurations helped me test my garbage collector for correctness as well as give some insight into the heap tracing.
  * Thankfully, my garbage collector did not corrupt the heap, no matter how often I ran it.
  * When running the garbage collector at every instruction, I collected some data to get the max heap footprint of each program:

  | Benchmark         | Memory Footprint (num elements) |
  | ----------------- | ------------------------------- |
  | major-elm         | 9                               |
  | quicksort-hoare   | 250                             |
  | two-sum           | 20                              |
  | adj2csr           | 3073                            |
  | quicksort         | 24                              |
  | quickselect       | 24                              |
  | max-subarray      | 20                              |
  | adler32           | 1024                            |
  | bubblesort        | 15                              |
  | binary-search     | 15                              |
  | fib               | 40                              |
  | sieve             | 200                             |

  You could probably accomplish even lower numbers if you applied some more dead code optimization passes.
  
* __Anything Hard or Interesting?__
  * I naively thought I could just use a function's environment as the roots, but I quickly released the garbage collector is more elaborate than that.
  * It is hard to not re-copy something from the "from space" to the "to space" twice. Otherwise you will triplicate some data and have pointers that should point to the same data that do not. I prevented this by performing garbage collection on the base pointers, not the offsets. Then I cached the translation 

* __References Used__
  * [Cheney's algorithm](https://en.wikipedia.org/wiki/Cheney%27s_algorithm)