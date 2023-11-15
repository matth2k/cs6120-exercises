# Lesson 12 Discussion

* __Summary__
  * [Code](https://github.com/matth2k/cs6120-exercises/blob/main/l13)
  * `usage: smt.py [-h] [-v] [-N BITS] expression`
  * Given some univariate expression using arithmetic, logical, and conditional operators, my solver will determine if it is (1) polynomial in variable `x` and equal to zero modulo 8.
  * This exercise was inspired by this by [Drane and Constantinides](https://cas.ee.ic.ac.uk/people/gac1/pubs/TheoDACKC11.pdf) on the formal verification of datapaths. In short, the paper uses the technique of "vanishing polynomials mod 2^k" to verify if a datapath and its optimized alternative are in fact equivalent. In my toy program, I only check if a polynomial vanishes modulo 2^3 = 8.

* __Implementation Details__
  * When working with RTL (register-transfer level), there are many instances where the logic you are writing depends on individual wires. For example, if wan to take an unsigned integer mod 16, you could write it as just taking the lower 4 bits of `number` as a bitslice: `wire[16:0] moduloEight = {12'h000, number[3:0]}`.
  * I also want to be able to represent exponents in my grammar, so that I can test polynomials themselves.
  * Given the last two points, it led me to augment the syntax with:
    * Bit slices like `x[3:0]`
    * Bit selection `x[1]`
    * Exponents `x^3` or `(x+1)^2`
    * Coefficents like `20x^2`
  * With the augmented syntax I can formulate the general form of a vanishing polynomial: `A*x*(x - 1)*(x - 2)*(x - 3) + 4*B*x*(x - 1)*(x - 2) + 4*C*x*(x - 1) + 8*D*x + 8*E`. `A` through `E` are my "holes." The derivation for this polynomial is on pages 5-7 of the reference.
    * This will not catch every single vanishing polynomial, because `A` is modeled as a bit vector, when really it can be its own polynomial in general. But close enough to find some interesting cases.
  * Finally, my program has an optional command line argument `-N <bits>` to specify the bit length of variable `x`, which can be any number greater than or equal to 8. 

* __Evaluation__

  Here are some interesting evaluations of my program:

  ```bash
  ~$ python3 smt.py "16x"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  16x
  ```
  ```
  ~$ python3 smt.py "x[3:0] ? (x[1] - 1 ? x[1] : 0) : x[2:0]"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  0
  ```
  ```
  ~$ python3 smt.py "((x[15:8] << 8) + x[7:0] - 1)^2 * (x << 1) * (x - 2)"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: Yes it is, with vanishing polynomial
  2x(x-1)(x-2)(x-3) + 4x(x-1)(x-2)
  ```
  ```
  ~$ python3 smt.py "((x[15:8] << 7) + x[7:0] - 1)^2 * (x << 1) * (x - 2)"
  Q: Is this expression polynomial in 'x' and zero modulo 8?
  A: No
  ```
  
  The last example becomes false if we set x to be sized 18

* __Anything Hard or Interesting?__
  * It was hard to get the associatively right on my polynomial parsing. However, having a out-of-the-box way to define a grammar is pretty cool. It's fun.
