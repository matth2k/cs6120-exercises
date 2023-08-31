import argparse
import sys
import json

from butils import *

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
