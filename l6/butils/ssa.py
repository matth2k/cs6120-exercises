from typing import Any
from butils.cfg import Instruction, CFG, Block
from butils.dominance import Dominance

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

        for var, insn in self.phi_nodes.items():
            i = start
            placed = False
            while (
                i < len(self.instrs)
                and "op" in self.instrs[i]
                and self.instrs[i]["op"] == "phi"
            ):
                if (
                    # This is a bad way of checking a match
                    self.instrs[i]["dest"] in insn.insn["dest"]
                    and self.instrs[i]["type"] == var[1]
                ):
                    self.instrs[i] = insn.insn
                    placed = True
                    break
                i += 1

            if not placed:
                self.instrs.insert(i, insn.insn)

    def rename_phi_node(self, var: tuple[str, Any], ssa_name: str) -> None:
        if var in self.phi_nodes:
            for insn in self.instrs:
                if "op" in insn and insn["op"] == "phi" and var[0] in insn["dest"]:
                    insn["dest"] = ssa_name
                    break

    def update_phi_arg(self, var: tuple[str, Any], label: str, ssa_name: str) -> None:
        if var in self.phi_nodes:
            for insn in self.instrs:
                if (
                    "op" in insn
                    and insn["op"] == "phi"
                    and var[0] in insn["dest"]
                    and label in insn["labels"]
                ):
                    insn["args"][insn["labels"].index(label)] = ssa_name
                    break

    def insert_phi_node(
        self, var: tuple[str, Any], ssa_name: str, source_name: str, blk_name: str
    ) -> None:
        if var not in self.phi_nodes:
            self.phi_nodes[var] = Instruction(
                {
                    "args": [source_name],
                    "dest": ssa_name if ssa_name is not None else var[0],
                    "labels": [blk_name],
                    "op": "phi",
                    "type": var[1],
                }
            )
        else:
            insn = self.phi_nodes[var].insn
            insn["args"].append(source_name)
            insn["labels"].append(blk_name)
            if ssa_name is not None:
                insn["dest"] = ssa_name


class SSA:
    def __init__(self, cfg: CFG) -> None:
        self.cfg = cfg
        self.successors = self.cfg.get_cfg()
        self.dom_info = Dominance(cfg)
        self.dom_frontier = self.dom_info.get_dom_frontier()
        self.blocks = cfg.get_blocks()
        self.variables = set()
        self.has_def_inside = {}
        self.ssa_blocks = {}

        # Collect all the variables in a set and track where vars have definitions
        for blk in self.blocks:
            blk_defs = blk.get_definitions_typed()
            self.variables = self.variables.union(blk_defs)
            for vdef in blk_defs:
                if vdef not in self.has_def_inside:
                    self.has_def_inside[vdef] = set([blk.get_name()])
                else:
                    self.has_def_inside[vdef].add(blk.get_name())

        # Change self.has_def_inside to contain lists
        # This will give more confidence when we mutate it while iterating over it
        for k in self.has_def_inside:
            self.has_def_inside[k] = list(self.has_def_inside[k])

        # Add args to set of variables
        # if "args" in cfg.func:
        #     for arg in cfg.func["args"]:
        #         self.variables.add(arg["name"])

        # Create SSA blocks
        for blk in self.blocks:
            self.ssa_blocks[blk.get_name()] = SSABlock(blk)

        for var in self.variables:
            if var in self.has_def_inside:
                for blk in self.has_def_inside[var]:
                    if blk in self.dom_frontier:
                        for front in self.dom_frontier[blk]:
                            blk_to_edit = self.ssa_blocks[front.get_name()]
                            blk_to_edit.insert_phi_node(var, None, var[0], blk)
                            # blk_to_edit.update_with_phi_nodes()
                            # Propagate the changes to blocks downstream
                            if front.get_name() not in self.has_def_inside:
                                self.has_def_inside[var].append(front.get_name())

        # Now rename across blocks
        self.ssa_names = {}
        self.ssa_name_stem = {}
        for var in self.variables:
            self.ssa_names[var[0]] = []
        #     self.ssa_name_stem[var[0] + ".0"] = var[0]
        #     self.ssa_name_stem[var[0]] = var[0]

        for _, ssa_blk in self.ssa_blocks.items():
            ssa_blk.update_with_phi_nodes()
        self.rename_recursively(self.ssa_blocks[self.blocks[0].get_name()])
        # Push changes to asm

        self.ssa_func = CFG.from_blocks(self.cfg.get_func(), self.blocks).get_func()

    def rename_recursively(self, blk: SSABlock, path: list[str] = []) -> None:
        # print("new call")
        name_stack = self.ssa_names.copy()
        for insn in blk.instrs:
            # Remap args
            if "args" in insn:
                for i in range(len(insn["args"])):
                    if insn["args"][i] not in self.ssa_name_stem:
                        continue
                    arg = self.ssa_name_stem[insn["args"][i]]
                    if arg in self.ssa_names:
                        insn["args"][i] = self.ssa_names[arg][-1][0]

            # SSA rename the dest
            if "dest" in insn:
                name_stem = (
                    self.ssa_name_stem[insn["dest"]]
                    if insn["dest"] in self.ssa_name_stem
                    else insn["dest"]
                )
                old_index = (
                    self.ssa_names[name_stem][-1][1]
                    if name_stem in self.ssa_names
                    and len(self.ssa_names[name_stem]) > 0
                    else -1
                )
                new_ssa_name = name_stem + "." + str(old_index + 1)
                self.ssa_names[name_stem].append((new_ssa_name, old_index + 1))
                self.ssa_name_stem[new_ssa_name] = name_stem
                insn["dest"] = new_ssa_name
                # print(f"Renaming {name_stem} on {insn} to {new_ssa_name} ({path})")

        for successor in self.successors[blk.get_name()]:
            ssa_blk = self.ssa_blocks[successor.get_name()]
            for var in ssa_blk.get_phi_nodes():
                if len(self.ssa_names[var[0]]) > 0:
                    ssa_blk.update_phi_arg(
                        var, blk.get_name(), self.ssa_names[var[0]][-1][0]
                    )

        # Propagate the simple name change to our dominated neighbors
        for other_blk in self.blocks:
            if self.dom_info.immediately_dominates(blk, other_blk):
                # print(f"Propagating {blk.get_name()} to {other_blk.get_name()}")
                self.rename_recursively(
                    self.ssa_blocks[other_blk.get_name()], path + [blk.get_name()]
                )

        self.ssa_names = name_stack

    def get_func(self) -> Any:
        return self.ssa_func.copy()
