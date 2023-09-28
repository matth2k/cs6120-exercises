import argparse
import sys
import json
from typing import Any

from butils.cfg import *
from butils.ssa import *

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
    non_ssa_funcs = [SSA.from_ssa(func).get_func() for func in brilProgram["functions"]]
    brilProgram["functions"] = non_ssa_funcs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)
