from __future__ import annotations
from typing import Generator, Any

BRANCH_OPS = ["br", "jmp"]
TERM_OPS = ["ret", "br", "jmp"]


class Block:
    def __init__(self, name: str, instrs: list[Any]) -> None:
        self.name = name
        self.instrs = instrs

    def get_name(self) -> str:
        return self.name

    def get_instrs(self) -> list[Any]:
        return self.instrs.copy()

    def get_terminator(self) -> Any:
        return self.instrs[-1].copy()

    def copy(self) -> Block:
        return Block(self.name, self.instrs.copy())

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def get_definitions(self) -> set[str]:
        defined = set()
        for insn in self.instrs:
            if "dest" in insn:
                defined.add(insn["dest"])
        return defined

    def get_arguments(self) -> set[str]:
        defined = set()
        args = set()
        for insn in self.instrs:
            if "args" in insn:
                for arg in insn["args"]:
                    if arg not in defined:
                        args.add(arg)

            if "dest" in insn:
                defined.add(insn["dest"])
        return args

    def get_kills(self) -> set[str]:
        used = set()
        kills = set()
        for insn in self.instrs:
            if "args" in insn:
                for arg in insn["args"]:
                    used.add(arg)

            if "dest" in insn:
                if insn["dest"] not in used:
                    kills.add(insn["dest"])

        return kills


class CFG:
    def __init__(self, func: Any) -> None:
        self.func = func.copy()
        # Generate blocks
        self.blocks = []
        anon_blk_count = 0
        cblk = []
        labelStack = []
        cname = "entry_blk"
        for insn in self.func["instrs"]:
            if "op" in insn:
                if len(labelStack) > 0:
                    if len(cblk) > 0:
                        self.blocks.append(Block(cname, cblk))
                        cblk = []
                    cname = labelStack[0]["label"]
                    cblk = labelStack
                    labelStack = []

                cblk.append(insn)
                if insn["op"] in TERM_OPS:
                    self.blocks.append(Block(cname, cblk))
                    cblk = []
                    anon_blk_count += 1
                    cname = f"fallthru_blk_{anon_blk_count}"
            elif "label" in insn:
                labelStack.append(insn)
            else:
                raise Exception(f"bad Instruction {insn}")

        if "type" in func and len(cblk) > 0:
            raise Exception(f"Func did not end on terminator")

        cblk += labelStack
        if len(cblk) > 0:
            self.blocks.append(Block(cname, cblk))

        self.blockDict = {}
        for blk in self.blocks:
            self.blockDict[blk.get_name()] = blk
            for insn in blk.get_instrs():
                if "label" in insn:
                    self.blockDict[insn["label"]] = blk

    def get_func(self) -> Any:
        return self.func.copy()

    def get_blocks(self) -> list[Block]:
        return self.blocks.copy()

    def get_block(self, name: str) -> Block:
        if name in self.blockDict:
            return self.blockDict[name]
        else:
            for blk in self.blocks:
                for insn in blk.get_instrs():
                    if "label" in insn and insn["label"] == name:
                        return blk

        raise Exception(f"Block {name} not found")

    def get_cfg(self) -> dict[str, list[Block]]:
        nameToSuccessors = {}
        for blk in self.blocks:
            nameToSuccessors[blk.get_name()] = []
        for s, d in self.get_cfg_edges():
            nameToSuccessors[self.get_block(s).get_name()].append(self.get_block(d))
        return nameToSuccessors

    def get_sink(self) -> Block:
        sink = None
        mycfg = self.get_cfg()
        for k, v in mycfg.items():
            if len(v) == 0:
                if sink is not None:
                    raise Exception("Can't have more than one sink")
                sink = self.get_block(k)

        return sink

    def get_predecessors(self) -> dict[str, list[Block]]:
        predDict = {}
        for blk in self.blocks:
            predDict[blk.get_name()] = []
        for p, k in self.get_cfg_edges():
            predDict[self.get_block(k).get_name()].append(self.get_block(p))
        return predDict

    def get_cfg_edges(self) -> Generator[tuple[str, str], None, None]:
        lastBlock = None
        for blk in self.blocks:
            term = blk.get_terminator()
            if "op" not in term:
                raise Exception(f"bad terminator {term}")

            if lastBlock is not None:
                yield lastBlock, blk.get_name()

            if term["op"] in BRANCH_OPS:
                for branch in term["labels"]:
                    yield blk.get_name(), branch
                lastBlock = None
            else:
                lastBlock = blk.get_name()

    def from_blocks(
        func,
        blks: list[Block],
        name: str = None,
        type: str = None,
        args: list[Any] = None,
    ) -> CFG:
        returnFunc = func.copy()
        returnFunc["instrs"] = []
        for blk in blks:
            returnFunc["instrs"] += blk.get_instrs()

        if name is not None:
            returnFunc["name"] = name
        if type is not None:
            returnFunc["type"] = type
        if args is not None:
            returnFunc["args"] = args

        return CFG(returnFunc)

    def from_list(
        func,
        ilist: list[Any],
        name: str = None,
        type: str = None,
        args: list[Any] = None,
    ) -> CFG:
        returnFunc = func.copy()
        returnFunc["instrs"] = ilist

        if name is not None:
            returnFunc["name"] = name
        if type is not None:
            returnFunc["type"] = type
        if args is not None:
            returnFunc["args"] = args
        return CFG(returnFunc)

    def get_instr_count(self) -> int:
        count = 0
        for insn in self.func["instrs"]:
            if "op" in insn:
                count += 1

        return count


def get_instr_count(program: Any) -> int:
    count = 0
    for func in program["functions"]:
        for insn in func["instrs"]:
            if "op" in insn:
                count += 1

    return count
