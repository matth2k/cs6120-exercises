import argparse
import sys
import json
from typing import Any

from butils.cfg import *
from butils.dataflow import *


def join(l: list[set]) -> set:
    if len(l) == 0:
        raise Exception("Cannot merge empty list of sets")
    return set().union(*l)


def meet(l: list[set]) -> set:
    if len(l) == 0:
        raise Exception("Cannot merge empty list of sets")
    return set.intersection(*l)


ANALYSES = {
    "liveness": DataFlow(
        merge=join,
        transfer=lambda s, b: b.get_arguments().union(s.difference(b.get_kills())),
        init=lambda: set(),
        reverse=True,
    ),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", dest="verbose", default=False, action="store_true"
    )
    parser.add_argument(
        "-a",
        "--analysis",
        dest="analysis",
        type=str,
        default="liveness",
        action="store",
        help="dataflow anaylsis to run",
    )
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    parser.add_argument(
        "output", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    args = parser.parse_args()
    if args.analysis not in ANALYSES:
        print(f"Invalid analysis option --analysis {args.analysis}", file=sys.stderr)
        sys.exit(1)

    brilProgram = json.load(args.input)

    dataflow = ANALYSES[args.analysis]
    if args.verbose:
        print(f"{sys.argv[0]}: Running analysis {args.analysis}", file=sys.stderr)
        print(f"{sys.argv[0]}: merge = {dataflow.merge.__name__}", file=sys.stderr)
        print(
            f'{sys.argv[0]}: transfer = "{dataflow.transfer.__name__}"', file=sys.stderr
        )
        print(f'{sys.argv[0]}: init = "{dataflow.transfer.__name__}"', file=sys.stderr)
        print(
            f'{sys.argv[0]}: direction = {"forward" if not dataflow.reverse else "backwards"}',
            file=sys.stderr,
        )
    print("functions", file=args.output)
    for func in brilProgram["functions"]:
        cfg = CFG(func)
        ins, outs = dataflow.solve(cfg, sys.stderr if args.verbose else None)
        print(f"  {func['name']}", file=args.output)
        for blk in cfg.get_blocks():
            print(f"    {blk.get_name()}", file=args.output)
            print(f"      in: {ins[blk.get_name()]}", file=args.output)
            print(f"      out: {outs[blk.get_name()]}", file=args.output)
