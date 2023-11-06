import argparse
import sys
import json

from butils.cfg import *


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

    brilProgram = json.load(args.input)
    cfgs = [CFG(func) for func in brilProgram["functions"]]

    result_funcs = [CFG.from_blocks(cfg.get_func(), [Block.merge_blocks(cfg.get_blocks())]).get_func() for cfg in cfgs]
    brilProgram["functions"] = result_funcs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)
