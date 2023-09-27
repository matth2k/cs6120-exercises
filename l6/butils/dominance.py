from collections import deque
from butils.cfg import Block, CFG


class Dominance:
    def __init__(self, cfg: CFG) -> None:
        self.cfg = cfg

        # Do process of elimination, so initialize all blocks to dominated by every other
        blocks = cfg.get_blocks()
        predecessors = cfg.get_predecessors()
        self.dom: dict[str, set] = {}
        self.dom[blocks[0].get_name()] = {blocks[0]}
        worklist = blocks.copy()
        worklist.remove(blocks[0])
        for b in worklist:
            self.dom[b.get_name()] = set(blocks)

        changing = True
        while changing:
            changing = False
            for b in worklist:
                precedingDom = set(blocks)
                for p in predecessors[b.get_name()]:
                    precedingDom = precedingDom.intersection(self.dom[p.get_name()])
                updatedDom = precedingDom.union(set([b]))
                if updatedDom != self.dom[b.get_name()]:
                    changing = True
                    self.dom[b.get_name()] = updatedDom

        # We have dominators now. Now do dominance Frontiers
        self.domFrontier: dict[str, set] = {}
        successors = cfg.get_cfg()
        for m in blocks:
            for dominator in self.dom[m.get_name()]:
                if dominator.get_name() not in self.domFrontier:
                    self.domFrontier[dominator.get_name()] = set()
                for s in successors[m.get_name()]:
                    if not self.strictly_dominates(dominator, s):
                        self.domFrontier[dominator.get_name()].add(s)

        # Finally, do dominator tree
        self.idom: dict[str, set] = {}
        for b in blocks:
            self.idom[b.get_name()] = set()
            for j in blocks:
                if not self.strictly_dominates(b, j):
                    continue

                # If k strictly dominates j, then it must also dom b, if b were the idom
                isIdom = True
                for k in blocks:
                    if (
                        k != b
                        and self.strictly_dominates(k, j)
                        and self.strictly_dominates(k, b)
                    ):
                        isIdom = False
                        break

                if not isIdom:
                    continue

                self.idom[b.get_name()].add(j)

    def get_dom_tree(self) -> dict[str, set]:
        cpyTree = {}
        for k, v in self.idom.items():
            cpyTree[k] = list(v)
        return cpyTree

    def get_dom_frontier(self) -> dict[str, list]:
        cpyFront = {}
        for k, v in self.domFrontier.items():
            cpyFront[k] = list(v)
        return cpyFront

    def dominates(self, a: Block, i: Block) -> bool:
        return a in self.dom[i.get_name()]

    def strictly_dominates(self, a: Block, i: Block) -> bool:
        return self.dominates(a, i) and a != i

    def immediately_dominates(self, a: Block, i: Block) -> bool:
        return i in self.idom[a.get_name()]

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
