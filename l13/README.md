# Lesson 13 Discussion

* __Summary__
  * Given some univariate expression written with arithmetic, logical, and conditional operators, my solver will determine if it is (1) polynomial in variable 'x' and (2)equal to zero modulo 8.
    * [Code](https://github.com/matth2k/cs6120-exercises/blob/main/l13)
    * `usage: smt.py [-h] [-v] [-N BITS] expression`
    * This exercise was inspired by [Drane and Constantinides](https://cas.ee.ic.ac.uk/people/gac1/pubs/TheoDACKC11.pdf) on the formal verification of datapaths. In short, the paper uses the technique of "vanishing polynomials mod 2^k" to verify if a datapath and its optimized alternative are in fact equivalent. In my toy program, I only check if a polynomial vanishes modulo 2^3.

* __Implementation Details__
  * When working with RTL (register-transfer level), there are many instances where the logic depends on individual wires. For example, if wanted to take an unsigned integer modulo 16, you could take the lower 4 bits of `number` as a bitslice and concatenate it with zeros: `wire[16:0] moduloEight = {12'h000, number[3:0]}`. Hence, I wanted to be able handle bitslicing in my application.
  * I also wanted to represent exponents, so that I can test polynomials themselves directly in my solver.
  * Given the last two points, it led me to augment the syntax with:
    * Bit slices like `x[3:0]`
    * Bit selection `x[1]`
    * Exponents like `x^3` or `(x+1)^2`
    * Coefficents like `20x` or `4x^2`
  * With the augmented syntax I can formulate the general form of a vanishing polynomial: `A*x*(x - 1)*(x - 2)*(x - 3) + 4*B*x*(x - 1)*(x - 2) + 4*C*x*(x - 1) + 8*D*x + 8*E`. `A` through `E` are my "holes." The derivation for this polynomial is on pages 5-7 of the [reference](https://cas.ee.ic.ac.uk/people/gac1/pubs/TheoDACKC11.pdf).
    * This will not catch every single vanishing polynomial, because `A` is modeled as a bit vector, when really it can be its own polynomial in general. But close enough to find some interesting cases.
  * Finally, my program has an optional command line argument `-N <bits>` to specify the bit length of variable `x`, which can be any number greater than or equal to 8. By default, I set it to 16.

* __Evaluation__

  We can start with polynomials that do vanish modulo 8, then scramble them up. Here are some interesting evaluations of my program:

  ```
  ~$ python3 smt.py "16x"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  16x
  ```
  Let's use a bunch of ternary operators in a bunch of ways that is still polynomial:
  ```
  ~$ python3 smt.py "x[3:0] ? (x[1] - 1 ? x[1] : 0) : x[2:0]"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  0
  ```
  Let's combine that with logical shift:
  ```
  ~$ python3 smt.py "((x[15:8] << 8) + x[7:0] - 1)^2 * (x << 1) * (x - 2)"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  2x(x-1)(x-2)(x-3) + 4x(x-1)(x-2)
  ```
  Let's sanity check by making the formula wrong:
  ```
  ~$ python3 smt.py "((x[15:8] << 7) + x[7:0] - 1)^2 * (x << 1) * (x - 2)"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: No
  ```
  
  The last example becomes false if we set x to be sized 18

* __Anything Hard or Interesting?__
  * It was hard to get the associatively right on my polynomial parsing. However, having a out-of-the-box way to define a grammar is pretty cool. It's fun.
