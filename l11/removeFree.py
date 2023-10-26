import argparse
import sys
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    parser.add_argument(
        "output", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    args = parser.parse_args()

    brilProgram = json.load(args.input)
    constPresent = set()

    for func in brilProgram["functions"]:
        newInstrs = []
        for insn in func["instrs"]:
            if "op" in insn and insn["op"] == "free":
                newInstrs.append(
                    {"dest": insn["args"][0], "op": "const", "type": "int", "value": 1}
                )
            else:
                newInstrs.append(insn)
        func["instrs"] = newInstrs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)
