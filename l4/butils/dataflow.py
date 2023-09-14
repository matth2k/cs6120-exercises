from butils.cfg import Block, CFG
from typing import Callable


class DataFlow:
    def __init__(
        self,
        merge: Callable[[list[set]], set],
        transfer: Callable[[set, Block], set],
        init: Callable[[], set],
        reverse: bool = False,
    ) -> None:
        self.merge = merge
        self.transfer = transfer
        self.init = init
        self.reverse = reverse

    def solve(self, cfg: CFG, verbosef=None) -> tuple[dict[str, set], dict[str, set]]:
        blocks = cfg.get_blocks()
        predecessors = cfg.get_predecessors()
        successors = cfg.get_cfg()
        if verbosef is not None:
            print(f"dataflow.py: Input CFG {successors}", file=verbosef)
        entry = blocks[0]
        sink = cfg.get_sink()
        ins = {}
        outs = {}
        if not self.reverse:
            ins = {entry.get_name(): self.init()}
            outs = {block.get_name(): self.init() for block in blocks}
        else:
            outs = {sink.get_name(): self.init()}
            ins = {block.get_name(): self.init() for block in blocks}
        # Why do we need to interate over the blocks?
        # Meet over all paths I think?
        worklist = blocks
        while len(worklist) > 0:
            b = worklist.pop()
            if verbosef is not None:
                print(f"dataflow.py: Visiting {b.get_name()}", file=verbosef)
            setsToMerge = []
            toVisit = (
                predecessors[b.get_name()]
                if not self.reverse
                else successors[b.get_name()]
            )
            for p in toVisit:
                setsToMerge.append(
                    outs[p.get_name()] if not self.reverse else ins[p.get_name()]
                )
            updatedInput = None
            oldOutput = None
            if not self.reverse:
                if len(setsToMerge) > 0:
                    ins[b.get_name()] = self.merge(setsToMerge)
                updatedInput = ins[b.get_name()]
                oldOutput = outs[b.get_name()]
            else:
                if len(setsToMerge) > 0:
                    outs[b.get_name()] = self.merge(setsToMerge)
                updatedInput = outs[b.get_name()]
                oldOutput = ins[b.get_name()]

            newOut = self.transfer(updatedInput, b)
            if newOut != oldOutput:
                if verbosef is not None:
                    print(
                        f"dataflow.py: Nontrivial transfer on {b.get_name()}",
                        file=verbosef,
                    )
                    print(f"  before: {oldOutput}", file=verbosef)
                    print(f"  after: {newOut}", file=verbosef)
                for s in (
                    successors[b.get_name()]
                    if not self.reverse
                    else predecessors[b.get_name()]
                ):
                    worklist.append(s)
            if not self.reverse:
                outs[b.get_name()] = newOut
            else:
                ins[b.get_name()] = newOut

        # Add optinal sort of sets for better printing
        useSorted = True
        inClone = {}
        outClone = {}
        for k, v in ins.items():
            sortedV = sorted(list(v))
            if sortedV is None or isinstance(v, dict):
                useSorted = False
                break
            inClone[k] = sortedV
        for k, v in outs.items():
            sortedV = sorted(list(v))
            if sortedV is None or isinstance(v, dict):
                useSorted = False
                break
            outClone[k] = sortedV
        return (ins, outs) if not useSorted else (inClone, outClone)
