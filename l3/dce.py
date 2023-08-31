import argparse
import sys
import json

from butils import *


def dce_block(block: list[Any]) -> tuple[list[Any], bool]:
    toKeep = set()
    for i, p in enumerate(block):
        if "dest" in p:
            for c in enumerate(block, start=i + 1):
                if "args" in c and p["dest"] in c["args"]:
                    toKeep.add(i)
                    break

    return [p for i, p in enumerate(block) if i in toKeep]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    args = parser.parse_args()

    brilProgram = json.load(args.input)

    for func in brilProgram["functions"]:
        blks = list(to_blocks(func))
        for blk in blks:
            print("blk")
            print(blk)
        edgelist = list(to_cfg_edges(blks))
        print(edgelist)
        print(to_cfg(blks))

        print(json.dumps(from_blocks(func, blks), indent=4))
