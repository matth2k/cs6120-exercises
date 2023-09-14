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


# Helper functions for interval analysis
def boundUnion(b1: tuple, b2: tuple[2]):
    return (
        min(b1[0], b2[0]) if b1[0] is not None and b2[0] is not None else None,
        max(b1[1], b2[1]) if b1[1] is not None and b2[1] is not None else None,
    )


def boundJoin(l: list[dict[str, tuple[Any, Any]]]) -> dict[str, tuple[Any, Any]]:
    d = l.pop()
    while len(l) > 0:
        q = l.pop()
        for k, v in q.items():
            if k in d:
                d[k] = boundUnion(d[k], v)
            else:
                d[k] = v

    return d


# Helpers for constant propagation
def constTransfer(s, b) -> dict[str, Any]:
    scopy = s.copy()
    scopy.update(b.get_constants())
    return scopy


def constMeet(l: list[dict[str, Any]]) -> dict[str, Any]:
    p = l.pop()
    while len(l) > 0:
        q = l.pop()
        for k, v in q.items():
            if k in p:
                if p[k] != v:
                    p[k] = None
            else:
                p[k] = v
    return p


# Helper functions for reaching definitions
def reachingJoin(l: list[dict[str, set]]) -> dict[str, set]:
    d = l.pop()
    while len(l) > 0:
        q = l.pop()
        for k, v in q.items():
            if k in d:
                d[k].union(v)
            else:
                d[k] = v
    return d


def reachingTransfer(s: dict[str, set], b):
    scopy = s.copy()
    killing_defs = b.get_killing_definitions()
    for k, _ in killing_defs.items():
        if k in scopy:
            scopy.pop(k, None)

    for k, v in b.get_definitions_dict().items():
        scopy[k] = set([v])
    return scopy


ANALYSES = {
    "liveness": DataFlow(
        merge=join,
        # live_in = gen U (live_out - kill)
        transfer=lambda s, b: b.get_arguments().union(s.difference(b.get_kills())),
        init=lambda: set(),
        reverse=True,
    ),
    "reaching": DataFlow(
        merge=reachingJoin,
        # reach_out = gen U (reach_in - kill)
        transfer=reachingTransfer,
        init=lambda: dict(),
        reverse=False,
    ),
    "defined": DataFlow(
        merge=join,
        transfer=lambda s, b: b.get_definitions().union(s),
        init=lambda: set(),
        reverse=False,
    ),
    "constants": DataFlow(
        merge=constMeet,
        transfer=constTransfer,
        init=lambda: dict(),
        reverse=False,
    ),
    "initialized": DataFlow(
        merge=meet,
        transfer=lambda s, b: b.get_definitions().union(s),
        init=lambda: set(),
        reverse=False,
    ),
    "interval": DataFlow(
        merge=boundJoin,
        transfer=lambda s, b: b.get_constant_intervals(s),
        init=lambda: dict(),
        reverse=False,
    ),
}

HELP_MSG = "There are 6 analyses available:\n'liveness' Live variable analysis\n'reaching' Reaching definitions analysis\n'defined' Get posibly defined variables\n'constants' Constant propagation anaylsis\n'initialized' Get guaranteed initialized variables\n'interval' Interval analysis"


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
        help=HELP_MSG,
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
