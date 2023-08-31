from typing import Generator, Any

branch_ops = ["br", "jmp"]
term_ops = ["ret", "br", "jmp"]


def to_blocks(func) -> Generator[tuple[str, list[Any]], None, None]:
    anon_blk_count = 0
    cblk = []
    labelStack = []
    cname = "entry_blk"
    for insn in func["instrs"]:
        if "op" in insn:
            if len(labelStack) > 0:
                if len(cblk) > 0:
                    yield cname, cblk
                    cblk = []
                cname = labelStack[0]["label"]
                cblk = labelStack
                labelStack = []

            cblk.append(insn)
            if insn["op"] in term_ops:
                yield cname, cblk
                cblk = []
                anon_blk_count += 1
                cname = f"fallthru_blk_{anon_blk_count}"
        elif "label" in insn:
            labelStack.append(insn)
        else:
            raise Exception(f"bad Instruction {insn}")

    if len(cblk) > 0:
        raise Exception(f"Program did not end on terminator")


def get_blk_name(blk: tuple[str, Any]) -> str:
    return blk[0]


def to_cfg(blocks: list[tuple[str, Any]]) -> dict[str, list[str]]:
    nameToSuccessors = {}
    for s, d in to_cfg_edges(blocks):
        if s not in nameToSuccessors:
            nameToSuccessors[s] = [d]
        else:
            nameToSuccessors[s] += [d]
    return nameToSuccessors


def to_cfg_edges(
    blocks: list[tuple[str, Any]]
) -> Generator[tuple[str, str], None, None]:
    lastBlock = None
    for label, blk in blocks:
        term = blk[-1]
        if "op" not in term:
            raise Exception(f"bad terminator {term}")

        if term["op"] in branch_ops:
            for branch in term["labels"]:
                yield label, branch
            lastBlock = None
        else:
            lastBlock = label

        if lastBlock is not None:
            yield lastBlock, label
