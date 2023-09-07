# Discussion


* __Summary__
  * [Trivial Dead Code Elimination](https://github.com/matth2k/cs6120-exercises/blob/main/l3/dce.py)
  * [Local Value Numbering Implementation with Clobbering & Constant Folding](https://github.com/matth2k/cs6120-exercises/blob/main/l3/lvn.py)
* __Implementation Details__
  * For TDCE, the implementation followed very closely to what we learned in lecture. Nothing particularly interesting to report.
  * LVN, on the other hand, took a lot of effort to create a solution that lent itself to robust constant folding.
    * Part of the strengh and weakness of my solution is that I created a class called `Expr`, which has four subclasses: `BinaryExpr`, `UnaryExpr`, `Const`, and `Value`. So in this case, an LVN number is a `Value` which is a type of sub-expression itself. If it can be folded, we do so, otherwise we use the `Value` expression at face value and use the LVN table to rewrite the output variable as an `id` operation. This allowed me to implement constant folding, but caused myself a lot of confusion on the fact that I changed the simple numbering algorithm to having `Value`'s be a sub-type of expressions.
    * Finally, I implemented clobbering by storing the canonical variables of a `Value` as an entire set. This way, when we clobber a variable in the table, we don't *always* have to make a new variable name. Only if we are about to lose the subexpression (i.e. there is only 1 canonical variable left), I rewrite the variable with an `id` operation.
* __Evaluation__
  * To test correctness of the transforms, I ran dce and lvn on all the benchmarks in the Bril repo and ensured they did not break: core, float, mem, and mixed.
  * As for testing the strength of my constant folding, I used every test in the `examples/test/lvn` and I was happy with the results I found. I could shortcircuit boolean logic and constant fold past clobbered variables.
  * ~~I did not see great speedups still. The greatest speedups where only because the application did not have many instructions in the first place.~~ Here are some highlights of my results:
  
  | App  | DCE % Speedup | DCE + LVN % Speedup
  | ------------- | ------------- | ------------- |
  | ray-sphere-insersecion  | 0.00% | 35.92% |
  | mandelbrot   | 0.00%  | 34.10%  |
  | bitshift     | 0.00%  | 29.34%  |
  | pow           | 5.56%  | 25.00% |
  | euler               | 0.05%  | 24.37%  |
  | pascals-row   | 4.79%  | 17.81%  |
  | two-sum       | 10.2%  | 16.33%  |

  * I also have no slowdowns, which is nice.

* __Anything Hard or Interesting?__
  * For some reason, it was confusing/challenging for me to understand if folding a `Value` expression was a different case than other types of `Expr`. The answer is that, the folding is the same, but Values have one less step of indirection in that a `Value` is already bound to a variable. In the end the logic goes like this
  * Case On
    * Case: An non-value `Expr` has a `Value` associated with it
      * Add this output as a canonical variable for the `Value` we found.
    * Case: We reuse a `Value` directly
      * Add this output as a canonical variable.
    * Case: This is a new `Expr`
      * Allocate a new `Value` for this expression and associate it with the new `Expr`