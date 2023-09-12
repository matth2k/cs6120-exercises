import argparse
import sys
import json
from typing import Any

from butils.cfg import *
from butils.dataflow import *

side_effects = []
show_deleted = False


def join(l: list[set]) -> set:
    if len(l) == 0:
        raise Exception("Cannot merge empty list of sets")
    return set().union(*l)


def meet(l: list[set]) -> set:
    if len(l) == 0:
        raise Exception("Cannot merge empty list of sets")
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

    def getLives(s, b):
        returnVal = b.get_arguments().union(s.difference(b.get_kills()))
        print(f"{b.get_name()} {s}", file=args.output)
        print(f"{b.get_name()} {returnVal}", file=args.output)
        return returnVal

    dataflowLive = DataFlow(
        merge=lambda l: join(l),
        transfer=getLives,
        init=lambda: set(),
        reverse=True,
    )
    print("functions", file=args.output)
    for func in brilProgram["functions"]:
        cfg = CFG(func)
        ins, outs = dataflowLive.solve(cfg)
        print(f"  {func['name']}", file=args.output)
        for blk in cfg.get_blocks():
            print(f"    {blk.get_name()}", file=args.output)
            print(f"      in: {ins[blk.get_name()]}", file=args.output)
            print(f"      out: {outs[blk.get_name()]}", file=args.output)
