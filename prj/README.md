# Project Proposal (Matt Hofmann and Yixiao Du)

## Background
TODO: give some background
  * [CalyxIR](https://calyxir.org/)
  * [MLIR](https://mlir.llvm.org/)
  * [Vitis HLS](https://www.xilinx.com/products/design-tools/vitis/vitis-hls.html)
  * AMC: TODO
  * Allo: TODO

## What will you do?

We will be integrating Allo, a domain-specific language for accelerator design, as a frontend to our own WIP accelerator tool flow. Over the past year, we have built out an intermediate representation and compiler for embedded memory on accelerators and we would like to use it from a high-level of design. In the end, we would want to evaluate our project against other established high-level synthesis tools, like Vitis HLS.

For example, we will describe both sparse and dense kernels in the Allo frontend, lower their descriptions to AMC memory structures, and finally compile the programs through the AMC + Calyx backend.

## How will you do it?

We will hook into Allo's APIs to emit a combination of MLIR dialects (SCF, Affine, Arith, Memref, AMC)

## How will you empirically measure success?

* We will observe advantages in representation between MLIR + AMC intermediate representation versus LLVM in terms of LOC and design effort.
* We compare PPA (power, performance, area) of our tool flow with other commercial HLS tools (Vitis HLS, maybe Catapult HLS).
* We will track how many new AMC bugs and issues are exposed via behavioural simulation through the Allo + LLVM backend.