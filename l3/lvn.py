import argparse
import sys
import json

from butils import *
from expr import *

show_folded = False


def insert_phi(instrs: list[Any]) -> list[Any]:
    defined = set()
    returnInstrs = []
    i = 0
    for insn in instrs:
        newInsn = insn.copy()
        newArgs = []
        if "args" in insn:
            for arg in insn["args"]:
                if arg not in defined:
                    phiName = "phi" + str(i)
                    returnInstrs.append(
                        {
                            "op": "id",
                            "dest": phiName,
                            "type": insn["type"],
                            "args": [arg],
                        }
                    )
                    defined.add(phiName)
                    newArgs.append(phiName)
                    i += 1
                else:
                    newArgs.append(arg)

            newInsn["args"] = newArgs

        if "dest" in insn:
            defined.add(insn["dest"])
        returnInstrs.append(newInsn)

    return returnInstrs


def blk_lvn(instrs: list[Any]) -> tuple[list[Any], bool]:
    returnInstrs = []
    modified = False
    val2Num = {}
    var2Num = {}
    num2Val = {}

    aliased_instrs = insert_phi(instrs)

    for insn in aliased_instrs:
        expr = Expr.from_instr(insn, var2Num)
        if expr is None:
            returnInstrs.append(insn)
            continue

        entry = (expr, set([insn["dest"]]))

        # Clobber for now. Later rename variables
        if insn["dest"] in var2Num:
            print("Clobbering", insn["dest"])
            num2Val[var2Num[insn["dest"]]][1].discard(insn["dest"])

        # Update LVM table
        if expr in val2Num:
            var2Num[insn["dest"]] = val2Num[expr]
            num2Val[val2Num[expr]][1].add(insn["dest"])
        else:
            val2Num[expr] = len(num2Val)

            var2Num[insn["dest"]] = len(num2Val)

            num2Val[len(num2Val)] = entry

        if "args" not in insn:
            returnInstrs.append(insn)
            continue

        # rewrite the instruction with latest table
        rewritten = insn.copy()
        remappedArgs = []
        for arg in insn["args"]:
            # get a canonical variable left in the set
            pval = num2Val[var2Num[arg]][1].pop()
            num2Val[var2Num[arg]][1].add(pval)
            remappedArgs.append(pval)

        rewritten["args"] = remappedArgs
        if rewritten != insn:
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
        show_folded = True

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

    json.dump(brilProgram, args.output, indent=2)
