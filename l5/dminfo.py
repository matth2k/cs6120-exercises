import argparse
import sys
import json
from typing import Any

from butils.cfg import *
from butils.dominance import *

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

    print("functions", file=args.output)
    for func in brilProgram["functions"]:
        print(f"  {func['name']}", file=args.output)
        cfg = CFG(func)
        domInfo = Dominance(cfg)
        print(f"    {domInfo.get_dom_tree()}", file=args.output)
