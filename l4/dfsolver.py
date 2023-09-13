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


# Four helper functions for interval analysis
def boundUnion(b1: tuple, b2: tuple[2]):
    return (
        min(b1[0], b2[0]) if b1[0] is not None and b2[0] is not None else None,
        max(b1[1], b2[1]) if b1[0] is not None and b2[0] is not None else None,
    )


def boundMeet(l: list[set]) -> set:
    p = l.pop()
    while len(l) > 0:
        mergedP = set()
        q = l.pop()
        for e in p:
            for f in q:
                if e[0] == f[0]:
                    mergedP.add((e[0], boundUnion(e[1], f[1])))
        p = mergedP
    return p


def boundJoin(l: list[set]) -> set:
    p = l.pop()
    while len(l) > 0:
        mergedP = set()
        q = l.pop()
        for e in p:
            added = False
            for f in q:
                if e[0] == f[0]:
                    mergedP.add((e[0], boundUnion(e[1], f[1])))
                    added = True
                else:
                    mergedP.add(f)
            if not added:
                mergedP.add(e)
        p = mergedP
    return p


def boundTransfer(s, b) -> set:
    consts = set()
    # TODO: actually implement this
    constantVars = b.get_definitions()
    for c in constantVars:
        consts.add((c, (1, 1)))
    return boundJoin([s, consts])


# Helper for constant propagation
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


ANALYSES = {
    "liveness": DataFlow(
        merge=join,
        # live_in = gen U (live_out - kill)
        transfer=lambda s, b: b.get_arguments().union(s.difference(b.get_kills())),
        init=lambda: set(),
        reverse=True,
    ),
    # TODO: need to use actual ops, not variable names
    "reaching": DataFlow(
        merge=join,
        # reach_out = gen U (reach_in - kill)
        transfer=lambda s, b: b.get_arguments().union(s.difference(b.get_kills())),
        init=lambda: set(),
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
    # TODO: implement
    "interval": DataFlow(
        merge=boundMeet,
        transfer=boundTransfer,
        init=lambda: set(),
        reverse=False,
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
