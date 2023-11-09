import argparse
import sys
import json

from butils.cfg import *


def makeSpeculativePath(cfg: CFG, blocksToMerge: list[Block]) -> list[Block]:
    functionBlocks = []
    cfgDict = cfg.get_cfg()
    cfg.make_jmp_explicit()
    for i, blk in enumerate(blocksToMerge):
        if i + 1 < len(blocksToMerge):
            if (
                blk.get_name() not in cfgDict
                or blocksToMerge[i + 1] not in cfgDict[blk.get_name()]
            ):
                raise Exception(
                    f"Not a valid path. No edge from {blk.get_name()} to {blocksToMerge[i + 1].get_name()}"
                )

    mergedBlock = Block.merge_blocks(blocksToMerge, cfg, True)
    for blk in cfg.get_blocks():
        if blocksToMerge[0] in cfgDict[blk.get_name()]:
            term = blk.get_terminator_mut()
            if "labels" in term:
                term["labels"] = [
                    l if l != blocksToMerge[0].get_name() else mergedBlock.get_name()
                    for l in term["labels"]
                ]
        if blk.get_name() == blocksToMerge[0].get_name():
            functionBlocks.append(mergedBlock)
        functionBlocks.append(blk)

    return functionBlocks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", dest="verbose", default=False, action="store_true"
    )
    parser.add_argument(
        "-f",
        "--function",
        dest="function",
        type=str,
        help="Which function the blocks belong to",
        default="main",
    )
    parser.add_argument(
        "-b",
        "--blocks",
        dest="blocks",
        type=str,
        nargs="*",
        help="A list of basic block names to mark as a hot path",
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

    result_funcs = []
    blockNames = list(args.blocks) if args.blocks is not None else []
    if args.verbose:
        print(
            f"{sys.argv[0]}: will try to merge following blocks {blockNames}",
            file=sys.stderr,
        )
    if blockNames is None or len(blockNames) < 2:
        print(f"{sys.argv[0]}: Need at least two blocks to merge", file=sys.stderr)
        sys.exit(1)

    thereWasAnError = True
    for cfg in cfgs:
        oldFunc = cfg.get_func()
        try:
            if oldFunc["name"] != args.function and args.function != "main":
                raise Exception(f"Wrong function name")
            blocksToMerge = [cfg.get_block(blkName) for blkName in blockNames]
            if None in blocksToMerge or len(blocksToMerge) <= 1:
                raise Exception(f"Invalid block list")
            functionBlocks = makeSpeculativePath(cfg, blocksToMerge)
            result_funcs.append(
                CFG.from_blocks(cfg.get_func(), functionBlocks).get_func()
            )
            if args.verbose:
                print(
                    f"{sys.argv[0]}: Good! {cfg.get_func()['name']}() has a speculative path now.",
                    file=sys.stderr,
                )
            thereWasAnError = False
        except Exception as e:
            if args.verbose:
                print(
                    f"{sys.argv[0]}: failed to merge blocks in function {cfg.get_func()['name']}(). Reason {e}. Skipping...",
                    file=sys.stderr,
                )
            result_funcs.append(oldFunc)
    brilProgram["functions"] = result_funcs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)

    if thereWasAnError:
        sys.exit(1)
