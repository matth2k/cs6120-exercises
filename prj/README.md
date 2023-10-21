# Frontend Integration for AMC (Accelerator Memory Compiler) - Matt Hofmann and Yixiao Du

## Background
Our research area is in accelerator design, HLS (high-level synthesis), and FPGA CAD tools in general. For our course project, we want to continue developing and evaluating our own open-source HLS tool flow as an alternative to commercial EDA tools. Here is a list of existing components belonging to our proposed flow:
  * [MLIR](https://mlir.llvm.org/) is a sub-project of LLVM that provides an extensible infrastructure for building new compilers cheaply and quickly.
  * [CalyxIR](https://calyxir.org/) is an IR and compiler for accelerator design lead by @rachitnigam and @sampsyo.
  * AMC (Accelerator Memory Compiler) is our new intermediate representation for accelerator memory embedded as a dialect within MLIR. It's purpose is to elaborate the missing constructs in software IRs needed to compile to spatial architectures. For example, LLVM's notion of memory can be summarized as loads and stores on pointers. AMC extends software IR to model embedded memory as used by hardware accelerators. In short, this means AMC IR has a notion of memory ports with latency, memory banks, arbiters, reuse buffers, etc.. 
  * Allo is a new Python-embedded DSL for designing accelerators in such a way that scheduling and memory customizations are decoupled from the algorithm specification itself. It is the successor to [HeteroCL](https://dl.acm.org/doi/10.1145/3289602.3293910).

## What will you do?

We will be integrating the Allo framework as a frontend to our own accelerator tool flow. Over the past year, our intermediate representation and compiler for embedded memory has matured, and we would like to leverage from a higher-level design language. In the end, we want to evaluate our project against other established high-level synthesis tools, like [Vitis HLS](https://www.xilinx.com/products/design-tools/vitis/vitis-hls.html).

To give an example, we would like to design both sparse and dense kernels in the Allo frontend, lower their descriptions to AMC memory structures, and finally compile the programs through the AMC and Calyx backend. Then, we can evaluate PPA (power, performance, area) on varying designpoints leveraging different memory subsystem customizations.

## How will you do it?

Allo's APIs already emit a combination of MLIR dialects (SCF, Affine, Arith, Memref). We will augment these APIs to also emit AMC IR. However, AMC fundamentally follows a different programming paradigm, because it actually details an entire memory micro-architecture. Hence, much of Allo's memory customizations will need to be rewritten.

## How will you empirically measure success?

These are the metrics we hope to show improvements on compared to C-based HLS:
* increased throughput
* reduced LOC (lines of code)
* faster compile times
* faster RTL simulation
* a wider and more incremental design space for exploring PPA (power, performance, area) tradeoffs
* number of AMC bugs caught as a result of faster design turnaround times
