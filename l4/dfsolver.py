import argparse
import sys
import json
from typing import Any

from butils.cfg import *
from butils.dataflow import *

side_effects = []
show_deleted = False


def join(l: list[set]) -> set:
    return set().union(*l)


def meet(l: list[set]) -> set:
    return set.intersection(*l)


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

    dataflowLive = DataFlow(
        merge=lambda l: join(l),
        transfer=lambda s, b: s.union(b.get_live_vars()),
        init=lambda: set(),
    )
    for func in brilProgram["functions"]:
        cfg = CFG(func)
        liveVars = dataflowLive.solve(cfg)
        print(liveVars, file=args.output)
