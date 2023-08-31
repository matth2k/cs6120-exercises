# Discussion

* __Summary__
  * [BRIL Benchmark PR](https://github.com/sampsyo/bril/pull/260)
  * [My new Bril tool](https://github.com/matth2k/cs6120-exercises/blob/main/l2/countBits.py)
* __Implementation Details__
  * I used the `ts2bril` tool to generate my benchmark from TypeScript. The benchmark itself is the [CORDIC algorithm](https://en.wikipedia.org/wiki/CORDIC) which can be used to approximate sine and cosine.
  * My bril tool uses Python to parse the json and count how many bits need to be allocated for constant values. Maybe you want an estimate of the size of the read-only data section when compiling. The tool also then calculates how many bits of space can be saved by elminating redundant `const` values. Here is an example output running on my CORDIC benchmark:
  ```
  $: python3 countBits.py cordic.json
  There are 1984 bits-worth of constants used in the program.
  If you remove duplicates values, only 1088 bits-worth of constants used in the program.
  ```
* __Anything Hard or Interesting?__
  * I wanted to use a constant array in my program from the TypeScript frontend. However, I noticed that arrays are an extension to both the `ts2bril` tool and the Bril IR. The main issue I ran into is that I did not know how to initialize my Bril memory through the TypeScript frontend. I wanted to use the normal syntax of `let myArray: number[] = [1, 2, ...];`, but I could not figure out how.