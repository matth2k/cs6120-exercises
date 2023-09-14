from collections import deque
from butils.cfg import Block, CFG


class Dominance:
    def __init__(self, cfg: CFG) -> None:
        self.cfg = cfg
        blocks = cfg.get_blocks()
        predecessors = cfg.get_predecessors()
        successors = cfg.get_cfg()
        self.domTree: dict[str, set] = {}

        # Do process of elimination, so initialize all blocks to dominated by every other
        self.domTree[blocks[0].get_name()] = {blocks[0]}
        worklist = blocks.copy()
        worklist.remove(blocks[0])
        for b in worklist:
            self.domTree[b.get_name()] = set()

        while True:
            changed = False
            for b in worklist:
                precedingDom = set()
                for p in predecessors[b.get_name()]:
                    precedingDom = precedingDom.intersection(self.domTree[p.get_name()])
                updatedDom = precedingDom.union(set([b]))
                if updatedDom != self.domTree[b.get_name()]:
                    changed = True
                    self.domTree[b.get_name()] = updatedDom
            if not changed:
                return

    def get_dom_tree(self) -> dict[str, list]:
        cpyTree = {}
        for k, v in self.domTree.items():
            cpyTree[k] = list(v)
        return cpyTree

    def dominates(self, a: Block, i: Block) -> bool:
        return i in self.domTree[a.get_name()]
