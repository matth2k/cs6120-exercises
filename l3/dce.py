import argparse
import sys
import json

from butils import *

side_effects = []
show_deleted = False


def dce_block_out_dep(instrs: list[Any]) -> tuple[list[Any], bool]:
    isDead = set()

    returnInstrs = []
    modified = False
    for insn in reversed(instrs):
        if "dest" in insn:
            if insn["dest"] in isDead:
                modified = True
                if show_deleted:
                    print(f"Deleted {insn}", file=sys.stderr)
            else:
                returnInstrs.append(insn)
                isDead.add(insn["dest"])
        else:
            returnInstrs.append(insn)

        # We set liveness since we iterate backwards
        if "args" in insn:
            for arg in insn["args"]:
                isDead.discard(arg)

    returnInstrs = list(reversed(returnInstrs))
    return returnInstrs, modified


def dce_func_use_dep(instrs: list[Any], tillConverge=True) -> tuple[list[Any], bool]:
    useSet = set()
    returnInstrs = []
    modified = False
    for insn in instrs:
        if "args" in insn:
            for arg in insn["args"]:
                useSet.add(arg)

    for insn in instrs:
        if (
            "op" in insn
            and "dest" in insn
            and insn["dest"] not in useSet
            and insn["op"] not in side_effects
        ):
            modified = True
            if show_deleted:
                print(f"Deleted {insn}", file=sys.stderr)
        else:
            returnInstrs.append(insn)

    if not tillConverge or not modified:
        return returnInstrs, modified
    else:
        return dce_func_use_dep(returnInstrs, tillConverge)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-out-dep", dest="out_dep", action="store_false")
    parser.add_argument("--no-use-dep", dest="use_dep", action="store_false")
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
        show_deleted = True

    brilProgram = json.load(args.input)

    dceFuncs = (
        [
            from_list(f, dce_func_use_dep(f["instrs"])[0])
            for f in brilProgram["functions"]
        ]
        if args.use_dep
        else brilProgram["functions"]
    )

    outputFuncs = []
    if args.out_dep:
        for f in dceFuncs:
            dceBlks = []
            for b in list(to_blocks(f)):
                dceB = dce_block_out_dep(b[1])[0]
                if len(dceB) > 0:
                    dceBlks.append((b[0], dceB))
            outputFuncs.append(from_blocks(f, dceBlks))
    else:
        outputFuncs = dceFuncs

    before = get_instr_count(brilProgram)
    brilProgram["functions"] = outputFuncs
    after = get_instr_count(brilProgram)
    print(f"{sys.argv[0]}: Instructions deleted : {before - after}", file=sys.stderr)
    json.dump(brilProgram, args.output, indent=2)
