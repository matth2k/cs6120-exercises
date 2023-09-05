import argparse
import sys
import json
from collections import OrderedDict

from butils import *
from expr import *

show_lvn = False


def blk_lvn(instrs: list[Any]) -> tuple[list[Any], bool]:
    returnInstrs = []
    modified = False
    val2Num = {}
    var2Num = {}
    num2Val = {}

    for insn in instrs:
        expr = Expr.from_instr(insn, var2Num, num2Val)
        if expr is None:
            returnInstrs.append(insn)
            continue

        entry = (expr, OrderedDict({insn["dest"]: True}))

        # TODO: Clobber for now. Later rename variables
        if insn["dest"] in var2Num:
            num2Val[var2Num[insn["dest"]]][1][insn["dest"]] = False

        # Update LVM table
        if expr in val2Num:
            if show_lvn:
                print(
                    f"{sys.argv[0]}: Found {expr} as {val2Num[expr]} for {insn['dest']}",
                    file=sys.stderr,
                )
            var2Num[insn["dest"]] = val2Num[expr]
            num2Val[val2Num[expr]][1][(insn["dest"])] = True
        elif isinstance(expr, Value):
            if show_lvn:
                print(
                    f"{sys.argv[0]}: Reusing {expr} for {insn['dest']}",
                    file=sys.stderr,
                )
            var2Num[insn["dest"]] = expr
        else:
            if show_lvn:
                print(
                    f"{sys.argv[0]}: Adding {expr} as {Value(len(num2Val), insn['type'])} for {insn['dest']}",
                    file=sys.stderr,
                )
            val2Num[expr] = Value(len(num2Val), insn["type"])
            var2Num[insn["dest"]] = Value(len(num2Val), insn["type"])
            num2Val[Value(len(num2Val), insn["type"])] = entry

        if "args" not in insn:
            returnInstrs.append(insn)
            continue

        # rewrite the instruction with latest table
        rewritten = expr.to_instr(insn, var2Num, num2Val)
        if rewritten != insn:
            if show_lvn and "args" in rewritten and "args" in insn:
                print(
                    f"{sys.argv[0]}: Rewrote {insn['args']} to {rewritten['args']}",
                    file=sys.stderr,
                )
            modified = True

        returnInstrs.append(rewritten)

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
        show_lvn = True

    brilProgram = json.load(args.input)

    outputFuncs = []
    for f in brilProgram["functions"]:
        lvnBlks = []
        for b in list(to_blocks(f)):
            lvnB = blk_lvn(b[1])[0]
            if len(lvnB) > 0:
                lvnBlks.append((b[0], lvnB))
        outputFuncs.append(from_blocks(f, lvnBlks))

    brilProgram["functions"] = outputFuncs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)
