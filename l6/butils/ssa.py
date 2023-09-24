from collections import deque
from butils.cfg import Instruction, CFG
from butils.dominance import Dominance

# TODO: delete this
import json


class SSA:
    def __init__(self, cfg: CFG) -> None:
        self.cfg = cfg
        self.dom_frontier = Dominance(cfg).get_dom_frontier()
        self.blocks = cfg.get_blocks()
        self.variables = set()
        self.has_def_inside = {}

        # Collect all the variables in a set and track where vars have definitions
        for blk in self.blocks:
            blk_defs = blk.get_definitions()
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
        if "args" in cfg.func:
            for arg in cfg.func["args"]:
                self.variables.add(arg["name"])

        for var in self.variables:
            if var in self.has_def_inside:
                for blk in self.has_def_inside[var]:
                    if blk in self.dom_frontier:
                        for front in self.dom_frontier[blk]:
                            blk_to_edit = self.cfg.get_block(front.get_name())
                            phi_node = Instruction(
                                {
                                    "args": [var, var],
                                    "dest": var,
                                    "labels": ["one", "two"],
                                    "op": "phi",
                                    "type": "int",
                                }
                            )
                            blk_to_edit.insert_front(phi_node)
                            # Propagate the changes to blocks downstream
                            if front.get_name() not in self.has_def_inside:
                                self.has_def_inside[var].append(front.get_name())

        # Test what we have so far
        print(
            json.dumps(
                CFG.from_blocks(self.cfg.get_func(), self.cfg.get_blocks()).get_func(),
                indent=2,
                sort_keys=True,
            )
        )
