import argparse
from collections import defaultdict
import sys

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

    labelCount = defaultdict(lambda: defaultdict(int))
    trace = []
    for line in args.input.readlines():
        func, label = line.strip().split("-")
        labelCount[func][label] += 1
        trace.append((func, label))

    maxF, maxL, maxC = None, None, 0
    for func in labelCount:
        for label in labelCount[func]:
            if labelCount[func][label] > maxC:
                maxC = labelCount[func][label]
                maxF = func
                maxL = label

    hotPath = [maxL]
    hotPathOccur = maxC
    stillHot = True
    cycleLen = None
    # Keep iterating until we lose more than a quarter of the hotness
    while stillHot:
        nextLs = defaultdict(int)
        nextC = 0
        nextL = None
        windowSize = len(hotPath)
        for i in range(len(trace) - windowSize - 1):
            window = trace[i : i + windowSize]
            path = [l for _, l in window]
            if path == hotPath:
                nextLs[trace[i + windowSize][1]] += 1

        for label in nextLs:
            if nextLs[label] > nextC:
                nextL = label
                nextC = nextLs[label]

        stillHot = nextC >= hotPathOccur * 3 / 4
        if stillHot:
            if nextL == hotPath[0] and cycleLen is None:
                cycleLen = len(hotPath)
            hotPath.append(nextL)
            hotPathOccur = nextC

    for l in hotPath:
        print(l, file=args.output, end=" ")

    if args.verbose:
        print(
            f"{sys.argv[0]}: Found cycle of length {cycleLen if cycleLen is not None else len(hotPath)}",
            file=sys.stderr,
        )
