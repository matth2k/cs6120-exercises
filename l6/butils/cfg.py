from __future__ import annotations
from typing import Generator, Any
import json

BRANCH_OPS = ["br", "jmp"]
TERM_OPS = ["ret", "br", "jmp"]

BINARY_OPS = {
    "add": lambda a, b: a + b,
    "fadd": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "fmul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
    "fsub": lambda a, b: a - b,
    "div": lambda a, b: a / b,
    "fdiv": lambda a, b: a / b,
    "eq": lambda a, b: a == b,
    "feq": lambda a, b: a == b,
    "lt": lambda a, b: a < b,
    "flt": lambda a, b: a < b,
    "gt": lambda a, b: a > b,
    "fgt": lambda a, b: a > b,
    "le": lambda a, b: a <= b,
    "fle": lambda a, b: a <= b,
    "ge": lambda a, b: a >= b,
    "fge": lambda a, b: a >= b,
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
}

MONO_INCR_OPS = {
    "add": lambda a, b: a + b,
    "fadd": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "fmul": lambda a, b: a * b,
}

MONO_DECR_OPS = {
    "sub": lambda a, b: a - b,
    "fsub": lambda a, b: a - b,
    "div": lambda a, b: a / b,
    "fdiv": lambda a, b: a / b,
}


class Instruction:
    def __init__(self, insn: Any) -> None:
        self.insn = insn
        self.op = insn["op"] if "op" in insn else ""
        self.args = ""
        if "args" in insn:
            for arg in insn["args"]:
                self.args += f"{arg} "
        if "value" in insn:
            self.args += f" {insn['value']}"
        self.dest = insn["dest"] if "dest" in insn else None
        self.type = insn["type"] if "type" in insn else None

    def get_type(self) -> Any:
        return self.type

    def get_dest(self) -> str:
        return self.dest

    def __eq__(self, other) -> bool:
        return isinstance(other, Instruction) and self.insn == other.insn

    def __str__(self) -> str:
        return f"{self.op} {self.args}"

    def __repr__(self) -> str:
        return f"{self.op} {self.args}"

    def __hash__(self):
        return hash(json.dumps(self.insn))


class Block:
    def __init__(self, name: str, instrs: list[Any]) -> None:
        self.name = name
        self.instrs = instrs

    def get_name(self) -> str:
        return self.name

    def insert_front(self, insn: Instruction) -> None:
        start = 0
        while "label" in self.instrs[start]:
            start += 1
        self.instrs.insert(start, insn.insn)

    def get_instrs(self) -> list[Any]:
        return self.instrs.copy()

    def get_terminator(self) -> Any:
        ind = len(self.instrs) - 1
        while "label" in self.instrs[ind] and ind > 0:
            ind -= 1
        if "label" in self.instrs[ind]:
            return None
        return self.instrs[ind].copy()

    def copy(self) -> Block:
        return Block(self.name, self.instrs.copy())

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def get_uses(self) -> set[str]:
        all_uses = set()
        for insn in self.instrs:
            if "args" in insn:
                for arg in insn["args"]:
                    all_uses.add(arg)
        return all_uses

    def get_definitions(self) -> set[str]:
        return set(self.get_definitions_dict().keys())

    def get_definitions_typed(self) -> tuple[set[str], dict[str, Any]]:
        defined = {}
        for insn in self.instrs:
            if "dest" in insn:
                defined[insn["dest"]] = insn["type"]
        return set(defined.keys()), defined

    def get_definitions_dict(self) -> dict[str, Instruction]:
        defined = {}
        for insn in self.instrs:
            if "dest" in insn:
                defined[insn["dest"]] = Instruction(insn)
        return defined

    def replace_insn_with(self, new_insn: Instruction, pos: int) -> None:
        self.instrs[pos] = new_insn.insn

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
        return set(self.get_killing_definitions().keys())

    def get_killing_definitions(self) -> dict[str, Instruction]:
        used = set()
        kills = {}
        for insn in self.instrs:
            if "args" in insn:
                for arg in insn["args"]:
                    used.add(arg)

            if "dest" in insn:
                if insn["dest"] not in used:
                    kills[insn["dest"]] = Instruction(insn)

        return kills

    def get_constants(self) -> dict[str, Any]:
        constantVals = {}
        for insn in self.instrs:
            if "dest" in insn:
                if insn["op"] == "const":
                    constantVals[insn["dest"]] = insn["value"]
                else:
                    constantVals[insn["dest"]] = None
        return constantVals

    def get_constant_intervals(
        self, intervals: dict[str, tuple[Any, Any]] = {}
    ) -> dict[str, tuple[Any, Any]]:
        updatedIntervals = intervals.copy()
        for insn in self.instrs:
            if "dest" in insn:
                if insn["op"] == "const":
                    updatedIntervals[insn["dest"]] = (insn["value"], insn["value"])
                elif (
                    insn["op"] in MONO_INCR_OPS
                    and insn["args"][0] in updatedIntervals
                    and insn["args"][1] in updatedIntervals
                ):
                    operation = MONO_INCR_OPS[insn["op"]]
                    arg0 = insn["args"][0]
                    arg1 = insn["args"][1]
                    lb = (
                        None
                        if updatedIntervals[arg0][0] is None
                        or updatedIntervals[arg1][0] is None
                        else operation(
                            updatedIntervals[arg0][0], updatedIntervals[arg1][0]
                        )
                    )
                    ub = (
                        None
                        if updatedIntervals[arg0][1] is None
                        or updatedIntervals[arg1][1] is None
                        else operation(
                            updatedIntervals[arg0][1], updatedIntervals[arg1][1]
                        )
                    )
                    updatedIntervals[insn["dest"]] = (lb, ub)
                elif (
                    insn["op"] in MONO_DECR_OPS
                    and insn["args"][0] in updatedIntervals
                    and insn["args"][1] in updatedIntervals
                ):
                    operation = MONO_DECR_OPS[insn["op"]]
                    arg0 = insn["args"][0]
                    arg1 = insn["args"][1]
                    lb = (
                        None
                        if updatedIntervals[arg0][0] is None
                        or updatedIntervals[arg1][1] is None
                        else operation(
                            updatedIntervals[arg0][0], updatedIntervals[arg1][1]
                        )
                    )
                    ub = (
                        None
                        if updatedIntervals[arg0][1] is None
                        or updatedIntervals[arg1][0] is None
                        else operation(
                            updatedIntervals[arg0][1], updatedIntervals[arg1][0]
                        )
                    )
                    updatedIntervals[insn["dest"]] = (lb, ub)
                else:
                    updatedIntervals[insn["dest"]] = (None, None)
        return updatedIntervals


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
                    cname = labelStack[-1]["label"]
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

        # if "type" in func and len(cblk) > 0:
        #     raise Exception(f"Func did not end on terminator {func}")

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

    def get_successors_by_name(self) -> dict[str, list[str]]:
        nameToSuccessors = {}
        for blk in self.blocks:
            nameToSuccessors[blk.get_name()] = []
        for s, d in self.get_cfg_edges():
            nameToSuccessors[self.get_block(s).get_name()].append(d)
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
            if lastBlock is not None:
                yield lastBlock, blk.get_name()

            if term is None:
                lastBlock = blk.get_name()
            elif term["op"] in BRANCH_OPS:
                for branch in term["labels"]:
                    yield blk.get_name(), branch
                lastBlock = None
            else:
                lastBlock = blk.get_name()

    def copy(self) -> CFG:
        return CFG(self.func.copy())

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
