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

    # Maybe you to know how many bits are needed for the constants in your program.
    constantAllocSpace = 0
    for func in brilProgram["functions"]:
        for insn in func["instrs"]:
            if "op" in insn and insn["op"] == "const":
                # Bril ints are 64b
                if insn["type"] == "int":
                    constantAllocSpace += 64
                elif insn["type"] == "bool":
                    constantAllocSpace += 1

    print(
        f"There are {constantAllocSpace} bits worth of constants used in the program."
    )
