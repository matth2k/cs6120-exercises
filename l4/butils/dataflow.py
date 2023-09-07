from butils.cfg import Block, CFG
from typing import Callable


class DataFlow:
    def __init__(
        self,
        merge: Callable[[list[set]], set],
        transfer: Callable[[set, Block], set],
        init: Callable[[], set],
    ) -> None:
        self.merge = merge
        self.transfer = transfer
        self.init = init

    def solve(self, cfg: CFG) -> set:
        blocks = cfg.get_blocks()
        predecessors = cfg.get_predecessors()
        successors = cfg.get_cfg()
        ins = {blocks[0].get_name(): self.init()}
        outs = {block.get_name(): self.init() for block in blocks}
        sink = cfg.get_sink()

        # Why do we need to interate over the blocks?
        # Meet over all paths I think?
        worklist = blocks
        while len(worklist) > 0:
            b = worklist.pop()
            setsToMerge = []
            for p in predecessors[b.get_name()]:
                setsToMerge.append(outs[p.get_name()])
            ins[b.get_name()] = self.merge(setsToMerge)
            newOut = self.transfer(ins[b.get_name()], b)
            if newOut != outs[b.get_name()]:
                for s in successors[b.get_name()]:
                    worklist.append(s)

            outs[b.get_name()] = newOut

        return outs[sink.get_name()]
