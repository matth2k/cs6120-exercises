from typing import Any, Generator
from butils.cfg import Instruction, CFG, Block
from butils.dominance import Dominance


class SSABlock(Block):
    def __init__(self, block: Block, placed: bool = False) -> None:
        super().__init__(block.get_name(), block.instrs)
        # Store as k,v (varName, ssaPhiNodeInsn)
        self.phi_nodes = {}
        self.placed = placed
        for insn in self.instrs:
            if "op" in insn and insn["op"] == "phi":
                self.phi_nodes[insn["dest"]] = Instruction(insn)

    def pop_phi_nodes(self) -> Generator[tuple[str, str], None, None]:
        if not self.placed:
            raise Exception("Phi nodes not placed")
        for var in self.get_phi_nodes():
            self.instrs.remove(self.phi_nodes[var].insn)
            yield var, self.phi_nodes[var].insn

    def insert_explicit_jmp(self, successors) -> None:
        i = 0
        while (
            i < len(self.instrs) - 1
            and "label" in self.instrs[i]
            and "label" in self.instrs[i + 1]
        ):
            self.instrs.insert(
                i + 1,
                {"op": "jmp", "args": [], "labels": [self.get_name()]},
            )
            i += 2

        if self.get_terminator() is None and len(successors) == 1:
            self.insert_back(
                Instruction({"op": "jmp", "args": [], "labels": successors})
            )

    def get_phi_nodes(self) -> list[str]:
        return list(self.phi_nodes.keys())

    def get_last_preceding_label(self) -> str:
        i = 0
        while (
            i < len(self.instrs) - 2
            and "label" in self.instrs[i]
            and "label" in self.instrs[i + 1]
            and "label" in self.instrs[i + 2]
        ):
            i += 1

        if i < len(self.instrs) and "label" in self.instrs[i]:
            return self.instrs[i]["label"]

    def write_phi_nodes(self) -> None:
        phi_nodes = [n for _, n in self.phi_nodes.items()]
        phi_nodes.sort(key=lambda x: x.insn["dest"])
        if self.placed:
            raise Exception("Phi nodes already placed")

        start = 0
        while start < len(self.instrs) and "label" in self.instrs[start]:
            start += 1

        i = start
        for insn in phi_nodes:
            self.instrs.insert(i, insn.insn)
            i += 1
        self.placed = True

    def update_phi_arg(self, var: str, label: str, ssa_name: str, insert=True) -> None:
        if self.placed:
            raise Exception("Phi nodes already placed")
        if var in self.phi_nodes:
            insn = self.phi_nodes[var].insn
            if label in insn["labels"]:
                insn["args"][insn["labels"].index(label)] = ssa_name
            elif insert:
                insn["args"].append(ssa_name)
                insn["labels"].append(label)

    def update_phi_dest(self, var: str, type: Any, ssa_name: str = None) -> None:
        if self.placed:
            raise Exception("Phi nodes already placed")
        if var not in self.phi_nodes:
            self.phi_nodes[var] = Instruction(
                {
                    "args": [],
                    "dest": ssa_name if ssa_name is not None else var,
                    "labels": [],
                    "op": "phi",
                    "type": type,
                }
            )
        else:
            self.phi_nodes[var].insn["type"] = type
            self.phi_nodes[var].insn["dest"] = ssa_name if ssa_name is not None else var


class SSA:
    def __init__(self, cfg: CFG, verboseF=None) -> None:
        self.verboseF = verboseF
        self.cfg = SSA.reanchor_cfg(cfg)
        self.blocks = self.cfg.get_blocks()
        self.successors = self.cfg.get_successors_by_name()
        self.dom_info = Dominance(self.cfg)
        self.dom_frontier = self.dom_info.get_dom_frontier()
        self.dom_downstream = self.dom_info.dom_downstream()

        # Make SSA blocks
        self.entry_blk_name = self.blocks[0].get_name()
        self.blocks = [SSABlock(b) for b in self.blocks]
        self.blk_map = {b.get_name(): b for b in self.blocks}

        # Make sure entry block has a labe for executing phi nodes
        if "label" not in self.blocks[0].instrs[0]:
            self.blk_map[self.entry_blk_name].insert_front(
                Instruction({"label": self.entry_blk_name})
            )

        self.variables = set()
        self.varToType = {}
        self.has_def_inside = {}
        # Set set of variables and where definitions lie
        for blk in self.blocks:
            vdefs, typeMap = blk.get_definitions_typed()
            for var in vdefs:
                if var not in self.has_def_inside:
                    self.has_def_inside[var] = []
                self.variables.add(var)
                self.varToType[var] = typeMap[var]
                if blk.get_name() not in self.has_def_inside[var]:
                    self.has_def_inside[var].append(blk.get_name())

        # Create default stack for renaming
        self.ssa_stack = {}
        self.ssa_name_counter = {k: 0 for k in self.variables}
        self.name_stem = {k: k for k in self.variables}
        if "args" in self.cfg.func:
            for arg in self.cfg.func["args"]:
                self.varToType[arg["name"]] = arg["type"]
                self.ssa_stack[arg["name"]] = [arg["name"]]
                self.name_stem[arg["name"]] = arg["name"]

        # Insert the initial phi nodes
        for var in self.variables:
            for blk_name in self.has_def_inside[var]:
                for front_name in self.dom_frontier[blk_name]:
                    self.blk_map[front_name].update_phi_dest(var, self.varToType[var])
                    if front_name not in self.has_def_inside[var]:
                        self.has_def_inside[var].append(front_name)

        # Now do renaming
        self.rename_recursively(self.blk_map[self.entry_blk_name])

        for ssab in self.blocks:
            ssab.write_phi_nodes()
            ssab.insert_explicit_jmp(self.successors[ssab.get_name()])

        self.ssa_cfg = CFG.from_blocks(self.cfg.get_func(), self.blocks)
        self.ssa_func = self.ssa_cfg.get_func()

    def push_var(self, var: str) -> str:
        name_stem = self.name_stem[var]
        new_index = self.ssa_name_counter[name_stem]
        ssa_name = name_stem + "." + str(new_index)
        if self.verboseF is not None:
            print(f"Pushing {var} onto stack as {ssa_name}", file=self.verboseF)
        if name_stem not in self.ssa_stack:
            self.ssa_stack[name_stem] = []
        self.ssa_stack[name_stem].append(ssa_name)
        self.name_stem[ssa_name] = name_stem
        self.ssa_name_counter[name_stem] = new_index + 1
        return ssa_name

    def get_ssa_name(self, var: str) -> str:
        name_stem = self.name_stem[var]
        if name_stem not in self.ssa_stack or len(self.ssa_stack[name_stem]) == 0:
            return "__undefined"
        return self.ssa_stack[name_stem][-1]

    def rename_recursively(self, blk: SSABlock):
        old_stack = {k: list(v) for k, v in self.ssa_stack.items()}
        if self.verboseF is not None:
            print(f"Inside {blk.get_name()}", file=self.verboseF)

        # rename phi nodes with new element
        for var in blk.get_phi_nodes():
            blk.update_phi_dest(var, self.varToType[var], self.push_var(var))

        for insn in blk.instrs:
            if "args" in insn:
                newArgs = [self.get_ssa_name(arg) for arg in insn["args"]]
                insn["args"] = newArgs

            if "dest" in insn:
                insn["dest"] = self.push_var(insn["dest"])

        for successor_name in self.successors[blk.get_name()]:
            canon_name = self.cfg.get_block(successor_name).get_name()
            sblk = self.blk_map[canon_name]
            for var in sblk.get_phi_nodes():
                sblk.update_phi_arg(
                    var,
                    successor_name if successor_name != canon_name else blk.get_name(),
                    self.get_ssa_name(var),
                )

        dominatedL = sorted(self.dom_downstream[blk.get_name()])
        if self.verboseF is not None:
            print(
                f"Renaming {blk.get_name()} dominates {dominatedL}", file=self.verboseF
            )
        for dominated in dominatedL:
            self.rename_recursively(self.blk_map[dominated])

        self.ssa_stack = old_stack

    def get_func(self) -> Any:
        return self.ssa_func.copy()

    def reanchor_cfg(cfg: CFG) -> CFG:
        tcfg = cfg
        predecessors = tcfg.get_predecessors()
        blocks = tcfg.get_blocks()
        while len(predecessors[blocks[0].get_name()]) > 0:
            frontblock = blocks[0]
            instrs = [
                {"label": frontblock.get_name() + ".root"},
            ]
            if "args" in cfg.func:
                for arg in cfg.func["args"]:
                    instrs.append(
                        {
                            "op": "id",
                            "args": [arg["name"]],
                            "dest": arg["name"] + ".0",
                            "type": arg["type"],
                        }
                    )
            instrs.append({"op": "jmp", "args": [], "labels": [frontblock.get_name()]})
            redirect = Block(frontblock.get_name() + ".root", instrs)
            blks = tcfg.get_blocks()
            for blk in blks:
                for insn in blk.instrs:
                    if "args" in insn:
                        for i in range(len(insn["args"])):
                            insn["args"][i] = insn["args"][i] + ".0"
            tcfg = CFG.from_blocks(
                tcfg.get_func(), [redirect] + tcfg.get_blocks(), bundleLabels=True
            )
            predecessors = tcfg.get_predecessors()
            blocks = tcfg.get_blocks()
        return tcfg

    def from_ssa(func: Any) -> CFG:
        cfg = CFG(func)
        block_list = [SSABlock(b.copy(), True) for b in cfg.get_blocks()]
        new_blocks = {p.get_name(): p for p in block_list}
        for block in block_list:
            for _, phi_insn in block.pop_phi_nodes():
                for i, arg in enumerate(phi_insn["args"]):
                    label = phi_insn["labels"][i]
                    # if phi_insn["args"][i] == "__undefined":
                    #     continue
                    new_blocks[label].insert_back(
                        Instruction(
                            {
                                "op": "id",
                                "args": [phi_insn["args"][i]],
                                "dest": phi_insn["dest"],
                                "type": phi_insn["type"],
                            }
                        )
                    )
        return CFG.from_blocks(func, block_list)
