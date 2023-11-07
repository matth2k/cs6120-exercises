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
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    parser.add_argument(
        "output", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    args = parser.parse_args()

    brilProgram = json.load(args.input)
    cfgs = [CFG(func) for func in brilProgram["functions"]]

    result_funcs = []
    for cfg in cfgs:
        oldFunc = cfg.get_func()
        try:
            blocksToMerge = [cfg.get_block("for.cond.12"), cfg.get_block("for.body.12")]
            functionBlocks = makeSpeculativePath(cfg, blocksToMerge)
            result_funcs.append(
                CFG.from_blocks(cfg.get_func(), functionBlocks).get_func()
            )
        except Exception as e:
            print(
                f"Failed to merge blocks in function {cfg.get_func()['name']} {e}",
                file=sys.stderr,
            )
            result_funcs.append(oldFunc)
    brilProgram["functions"] = result_funcs

    json.dump(brilProgram, args.output, indent=2, sort_keys=True)
