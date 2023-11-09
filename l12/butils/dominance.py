from collections import deque
from butils.cfg import Block, CFG


class Dominance:
    def __init__(self, cfg: CFG) -> None:
        self.cfg = cfg

        # Do process of elimination, so initialize all blocks to dominated by every other
        blocks = cfg.get_blocks()
        predecessors = cfg.get_predecessors()
        self.dom: dict[str, set] = {}
        self.dom[blocks[0].get_name()] = {blocks[0].get_name()}
        worklist = blocks.copy()
        worklist.remove(blocks[0])
        for b in worklist:
            self.dom[b.get_name()] = set([b.get_name() for b in blocks])

        changing = True
        while changing:
            changing = False
            for b in worklist:
                precedingDom = set([b.get_name() for b in blocks])
                for p in predecessors[b.get_name()]:
                    precedingDom = precedingDom.intersection(self.dom[p.get_name()])
                updatedDom = precedingDom.union(set([b.get_name()]))
                if updatedDom != self.dom[b.get_name()]:
                    changing = True
                    self.dom[b.get_name()] = updatedDom

        # We have dominators now. Now do dominance Frontiers
        self.domFrontier: dict[str, set] = {}
        successors = cfg.get_cfg()
        for m in blocks:
            for dominator in self.dom[m.get_name()]:
                if dominator not in self.domFrontier:
                    self.domFrontier[dominator] = set()
                for s in successors[m.get_name()]:
                    if not (
                        dominator in self.dom[s.get_name()]
                        and dominator != s.get_name()
                    ):
                        self.domFrontier[dominator].add(s.get_name())

        # Finally, do dominator tree
        self.idom: dict[str, str] = {}
        for b in blocks:
            for j in blocks:
                if not self.strictly_dominates(b, j):
                    continue

                # b strictly dominates j

                # If k strictly dominates j, then it must also dom b, if b were the idom
                isIdom = True
                for k in blocks:
                    if self.strictly_dominates(k, j) and self.strictly_dominates(b, k):
                        isIdom = False
                        break

                if not isIdom:
                    continue

                self.idom[j.get_name()] = b.get_name()

    def get_dom_frontier(self) -> dict[str, list]:
        cpyFront = {}
        for k, v in self.domFrontier.items():
            cpyFront[k] = list(v)
        return cpyFront

    def dom_downstream(self) -> None:
        dominates_strictly = {k: set() for k in self.dom.keys()}
        for k, v in self.dom.items():
            for i in v:
                if i != k:
                    dominates_strictly[i].add(k)

        dominates_downstream = {k: set() for k in self.dom.keys()}
        for k, s in dominates_strictly.items():
            for v in s:
                dominates_downstream[k] = dominates_downstream[k].union(
                    dominates_strictly[v]
                )
        my_children = {k: set() for k in dominates_strictly.keys()}
        for k, s in dominates_strictly.items():
            for v in s:
                if v not in dominates_downstream[k]:
                    my_children[k].add(v)

        return my_children

    def dominates(self, a: Block, i: Block) -> bool:
        return a.get_name() in self.dom[i.get_name()]

    def strictly_dominates(self, a: Block, i: Block) -> bool:
        return self.dominates(a, i) and a != i

    def immediately_dominates(self, a: Block, i: Block) -> bool:
        return i.get_name() in self.idom and a.get_name() == self.idom[i.get_name()]

    def verify(self) -> bool:
        successors = self.cfg.get_cfg()
        blocks = self.cfg.get_blocks()
        # A dominates B means iff all paths rooted at Entry containing B, also contains A

        # Do a DFS
        list = deque()
        list.append([blocks[0]])
        while len(list) > 0:
            path = list.popleft()
            print(path)
            d = path[-1]

            for p in path:
                for b in blocks:
                    if self.dominates(b, p) and not b in path:
                        return False

            for s in successors[d.get_name()]:
                # Finds all cycles
                if s not in path:
                    list.append(path + [s])

        return True
