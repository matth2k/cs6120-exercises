import argparse
import sys
import json

from butils import *

side_effects = []
show_folded = False
binary_ops = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
    "div": lambda a, b: a / b,
    "eq": lambda a, b: a == b,
    "lt": lambda a, b: a < b,
    "gt": lambda a, b: a > b,
    "le": lambda a, b: a <= b,
    "ge": lambda a, b: a >= b,
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
}
unary_ops = {
    "not": lambda a: not a,
}


def fold_op(insn: Any, dict: dict[str, Any]) -> Any:
    returnOp = insn.copy()
    if "op" not in insn or "args" not in insn or len(insn["args"]) < 1:
        if "dest" in insn:
            dict[insn["dest"]] = returnOp
        return returnOp

    folded = []
    for arg in insn["args"]:
        # For now don't recurse, because we are going to iterate in order
        if arg not in dict:
            if "dest" in insn:
                dict[insn["dest"]] = returnOp
            if show_folded:
                print(f"{sys.argv[0]}: Cannot fold {insn}", file=sys.stderr)
            return returnOp
        folded.append(dict[arg])

    argsConstant = True
    for arg in folded:
        if (
            "op" not in arg
            or arg["op"] != "const"
            or "type" not in arg
            or arg["type"] == "float"
        ):
            argsConstant = False
            break

    if argsConstant and "type" in insn:
        if insn["op"] in binary_ops:
            operand0 = folded[0]["value"]
            operand1 = folded[1]["value"]
            type0 = folded[0]["type"]
            type1 = folded[0]["type"]
            returnOp = {
                "op": "const",
                "value": binary_ops[insn["op"]](
                    eval(f"{type0}({operand0})"), eval(f"{type1}({operand1})")
                ),
                "dest": insn["dest"],
                "type": insn["type"],
            }
        elif insn["op"] in unary_ops:
            operand0 = folded[0]["value"]
            type0 = folded[0]["type"]
            returnOp = {
                "op": "const",
                "value": unary_ops[insn["op"]](eval(f"{type0}({operand0})")),
                "dest": insn["dest"],
                "type": insn["type"],
            }

    if "dest" in insn:
        dict[insn["dest"]] = returnOp
    return returnOp


def blk_fold(instrs: list[Any]) -> tuple[list[Any], bool]:
    returnInstrs = []
    modified = False
    dict = {}
    for insn in instrs:
        folded = fold_op(insn, dict)
        if folded != insn:
            modified = True
            if show_folded:
                print(f"{sys.argv[0]}: Folded {insn} to {folded}", file=sys.stderr)
        returnInstrs.append(folded)

    return returnInstrs, modified


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", dest="verbose", default=False, action="store_true"
    )
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    parser.add_argument(
        "output", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    args = parser.parse_args()
    if args.verbose:
        show_folded = True

    brilProgram = json.load(args.input)

    outputFuncs = []
    for f in brilProgram["functions"]:
        dceBlks = []
        for b in list(to_blocks(f)):
            dceB = blk_fold(b[1])[0]
            if len(dceB) > 0:
                dceBlks.append((b[0], dceB))
        outputFuncs.append(from_blocks(f, dceBlks))

    brilProgram["functions"] = outputFuncs

    json.dump(brilProgram, args.output, indent=2)
