from typing import Any
from butils.cfg import Instruction, CFG, Block
from butils.dominance import Dominance
from copy import deepcopy

# TODO: delete this
import json


class SSABlock(Block):
    def __init__(self, block: Block) -> None:
        super().__init__(block.get_name(), block.instrs)
        # Store as k,v (varName, ssaPhiNodeInsn)
        self.phi_nodes = {}

    def get_phi_nodes(self) -> list[tuple[str, Any]]:
        return list(self.phi_nodes.keys())

    def update_with_phi_nodes(self) -> None:
        start = 0
        while start < len(self.instrs) and "label" in self.instrs[start]:
            start += 1

        for _, insn in self.phi_nodes.items():
            i = start
            placed = False
            while (
                i < len(self.instrs)
                and "op" in self.instrs[i]
                and self.instrs[i]["op"] == "phi"
            ):
                if (
                    # TODO: This is a bad way of checking a match
                    self.instrs[i]["dest"]
                    in insn.insn["dest"]
                ):
                    self.instrs[i] = insn.insn
                    placed = True
                    break
                i += 1

            if not placed:
                self.instrs.insert(i, insn.insn)
                start += 1

    def rename_phi_node(self, var: str, ssa_name: str) -> None:
        if var in self.phi_nodes:
            for insn in self.instrs:
                if "op" in insn and insn["op"] == "phi" and var in insn["dest"]:
                    insn["dest"] = ssa_name
                    self.phi_nodes[var].insn = insn.copy()
                    break

    def update_phi_arg(self, var: str, label: str, ssa_name: str) -> None:
        if var in self.phi_nodes:
            insn = self.phi_nodes[var].insn
            if label in insn["labels"]:
                insn["args"][insn["labels"].index(label)] = ssa_name
            else:
                insn["args"].append(ssa_name)
                insn["labels"].append(label)

    def alloc_phi_node(self, var: str, type: Any, ssa_name: str = None) -> None:
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

    def insert_phi_node(
        self, var: str, type: Any, ssa_name: str, source_name: str, blk_name: str
    ) -> None:
        if var not in self.phi_nodes:
            self.phi_nodes[var] = Instruction(
                {
                    "args": [source_name],
                    "dest": ssa_name if ssa_name is not None else var,
                    "labels": [blk_name],
                    "op": "phi",
                    "type": type,
                }
            )
        elif blk_name not in self.phi_nodes[var].insn["labels"]:
            insn = self.phi_nodes[var].insn
            insn["args"].append(source_name)
            insn["labels"].append(blk_name)
            if ssa_name is not None:
                insn["dest"] = ssa_name
            self.phi_nodes[var].insn = insn
        else:
            insn = self.phi_nodes[var].insn
            index = insn["labels"].index(blk_name)
            insn["args"][index] = source_name
            if ssa_name is not None:
                insn["dest"] = ssa_name
            self.phi_nodes[var].insn = insn


class SSA:
    def __init__(self, cfg: CFG, verboseF=None) -> None:
        self.cfg = cfg
        self.successors = self.cfg.get_cfg()
        self.dom_info = Dominance(cfg)
        self.dom_frontier = self.dom_info.get_dom_frontier()
        self.blocks = cfg.get_blocks()
        self.variables = set()
        self.varToType = {}
        self.has_def_inside = {}
        self.ssa_blocks = {}
        self.verboseF = verboseF

        # Collect all the variables in a set and track where vars have definitions
        for blk in self.blocks:
            blk_defs = blk.get_definitions_typed()
            for vdef in blk_defs:
                self.variables.add(vdef[0])
                self.varToType[vdef[0]] = vdef[1]
                if vdef[0] not in self.has_def_inside:
                    self.has_def_inside[vdef[0]] = set([blk.get_name()])
                else:
                    self.has_def_inside[vdef[0]].add(blk.get_name())

        # Add args to set of variables
        func_args = []
        if "args" in cfg.func:
            for arg in cfg.func["args"]:
                var = arg["name"]
                func_args.append(var)
                self.variables.add(var)
                self.varToType[var] = arg["type"]
                if var in self.has_def_inside:
                    self.has_def_inside[var].add(self.blocks[0].get_name())
                else:
                    self.has_def_inside[var] = set([self.blocks[0].get_name()])

        # Change self.has_def_inside to contain lists
        # This will give more confidence when we mutate it while iterating over it
        for k in self.has_def_inside:
            self.has_def_inside[k] = list(self.has_def_inside[k])

        # Create SSA blocks
        for blk in self.blocks:
            self.ssa_blocks[blk.get_name()] = SSABlock(blk)

        # Make sure entry block has a phi node
        self.ssa_blocks[self.blocks[0].get_name()].insert_front(
            Instruction({"label": self.blocks[0].get_name()})
        )

        for var in self.variables:
            if var in self.has_def_inside:
                for blk in self.has_def_inside[var]:
                    if blk in self.dom_frontier:
                        if self.verboseF is not None and len(self.dom_frontier[blk]) > 0:
                            print(
                                f"{self.dom_frontier[blk]} are on the frontier of {blk} for variable {var}",
                                file=self.verboseF,
                            )
                        for front in self.dom_frontier[blk]:
                            blk_to_edit = self.ssa_blocks[front.get_name()]
                            blk_to_edit.alloc_phi_node(
                                var,
                                self.varToType[var],
                            )
                            # Propagate the changes to blocks downstream
                            if front.get_name() not in self.has_def_inside[var]:
                                self.has_def_inside[var].append(front.get_name())

        # Now rename across blocks
        ssa_names = {}
        self.ssa_name_stem = {}
        for var in self.variables:
            ssa_names[var] = []
            self.ssa_name_stem[var + ".0"] = var
            self.ssa_name_stem[var] = var

        if "args" in cfg.func:
            for arg in cfg.func["args"]:
                ssa_names[arg["name"]].append((arg["name"], 0))

        for _, ssa_blk in self.ssa_blocks.items():
            ssa_blk.update_with_phi_nodes()

        self.rename_recursively(
            self.ssa_blocks[self.blocks[0].get_name()], deepcopy(ssa_names)
        )

        self.ssa_func = CFG.from_blocks(self.cfg.get_func(), self.blocks).get_func()

    def rename_recursively(
        self, blk: SSABlock, ssa_names, path: list[str] = []
    ) -> None:
        for insn in blk.instrs:
            # Remap args
            if "args" in insn and not ("op" in insn and insn["op"] == "phi"):
                for i in range(len(insn["args"])):
                    arg_stem = self.ssa_name_stem[insn["args"][i]]
                    insn["args"][i] = ssa_names[arg_stem][-1][0]

            # SSA rename the dest
            if "dest" in insn:
                name_stem = self.ssa_name_stem[insn["dest"]]
                new_ssa_name = name_stem + "." + str(len(ssa_names[name_stem]))
                ssa_names[name_stem].append((new_ssa_name, len(ssa_names[name_stem])))
                self.ssa_name_stem[
                    name_stem + "." + str(len(ssa_names[name_stem]))
                ] = name_stem
                insn["dest"] = new_ssa_name
                if "op" in insn and insn["op"] == "phi" and self.verboseF is not None:
                    print(f"renamed isn {insn}", file=self.verboseF)

        for successor in self.successors[blk.get_name()]:
            ssa_blk = self.ssa_blocks[successor.get_name()]
            for var in ssa_blk.get_phi_nodes():
                name_stem = self.ssa_name_stem[var]
                if len(ssa_names[name_stem]) == 0:
                    ssa_names[name_stem].append((name_stem + ".0", 0))
                    self.ssa_name_stem[
                        name_stem + "." + str(len(ssa_names[name_stem]))
                    ] = name_stem

                ssa_blk.update_phi_arg(
                    var,
                    blk.get_name(),
                    ssa_names[name_stem][-1][0],
                )
                if self.verboseF is not None:
                    print(
                        f"Block {blk.get_name()} wants to output to {successor.get_name()}",
                        file=self.verboseF,
                    )

        # Propagate the simple name change to our dominated neighbors
        idoms = list(self.dom_info.idom[blk.get_name()])
        for other_blk in idoms:
            if self.verboseF is not None:
                print(
                    f"Block {blk.get_name()} wants to rename {other_blk.get_name()} with {ssa_names}",
                    file=self.verboseF,
                )
            self.rename_recursively(
                self.ssa_blocks[other_blk.get_name()],
                deepcopy(ssa_names),
                path + [blk.get_name()],
            )

    def get_func(self) -> Any:
        return self.ssa_func.copy()
