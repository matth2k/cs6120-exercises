import argparse
import sys
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    args = parser.parse_args()

    brilProgram = json.load(args.input)
    constPresent = set()

    # Maybe you to know how many bits are needed for the constants in your program.
    constantAllocSpace = 0
    for func in brilProgram["functions"]:
        for insn in func["instrs"]:
            if "op" in insn and insn["op"] == "const":
                # Bril ints are 64b
                if insn["type"] == "int" or insn["type"] == "float":
                    constantAllocSpace += 64
                    constPresent.add((insn["value"], 64))
                elif insn["type"] == "bool":
                    constantAllocSpace += 1
                    constPresent.add((insn["value"], 1))

    print(
        f"There are {constantAllocSpace} bits-worth of constants used in the program."
    )

    # Now calculate, subtracting repeated values
    constantAllocSpace = 0
    for const in constPresent:
        constantAllocSpace += const[1]

    print(
        f"If you remove duplicates values, only {constantAllocSpace} bits-worth of constants used in the program."
    )
