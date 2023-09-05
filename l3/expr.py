from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod


class Expr(ABC):
    @abstractmethod
    def fold(self):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, obj):
        foldSelf = self.fold()
        foldObj = obj.fold()
        return type(foldSelf) == type(foldObj) and foldSelf.__dict__ == foldObj.__dict__

    # dict will be var2Num
    def from_instr(instr: Any, dict: dict = None) -> Expr:
        if "dest" not in instr:
            return None
        if instr["op"] == "const":
            return Const(instr["value"], instr["type"])

        if dict is not None:
            if "args" in instr:
                for arg in instr["args"]:
                    if arg not in dict:
                        return None

        if instr["op"] in BinaryExpr.binary_ops:
            return BinaryExpr(
                instr["op"],
                tuple(arg if dict is None else dict[arg] for arg in instr["args"]),
                instr["type"],
            ).fold()
        if instr["op"] in UnaryExpr.unary_ops:
            return UnaryExpr(
                instr["op"],
                tuple(arg if dict is None else dict[arg] for arg in instr["args"]),
            ).fold()

        return None


class BinaryExpr(Expr):
    binary_ops = {
        "add": lambda a, b: a + b,
        "mul": lambda a, b: a * b,
        "sub": lambda a, b: a - b,
        "div": lambda a, b: a / b,
        "eq": lambda a, b: a == b,
        "lt": lambda a, b: a < b,
        "gt": lambda a, b: a > b,
        "le": lambda a, b: a <= b,
        "ge": lambda a, b: a >= b,
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
    }
    commutative_ops = {"add", "mul", "eq", "and", "or"}

    def __init__(self, op, args: tuple[Any], type: str):
        self.op = op
        self.args = args
        self.type = type

    def fold(self) -> Expr:
        if self.op in self.commutative_ops and self.type != "float":
            newArgs = list(self.args).sort()
            if newArgs is not None:
                return BinaryExpr(self.op, tuple(newArgs), self.type)

        return BinaryExpr(self.op, self.args, self.type)

    def __str__(self) -> str:
        return f"{self.op} #{self.args[0]}, #{self.args[1]}"


class Value(Expr):
    def __init__(self, val: Any):
        self.val = val

    def fold(self) -> Expr:
        return Value(self.val)

    def __lt__(self, obj):
        return self.val < obj.val

    def __str__(self) -> str:
        return f"#{self.val}"


class Const(Expr):
    def __init__(self, val: Any, type: str):
        self.val = val
        self.type = type

    def fold(self) -> Expr:
        return Const(self.val, self.type)

    def __str__(self) -> str:
        return f"const {self.val} : {self.type}"


class UnaryExpr(Expr):
    unary_ops = {"not": lambda a: not a, "id": lambda a: a}

    def __init__(self, op, arg: Any):
        self.op = op
        self.args = tuple(arg)

    def fold(self) -> Expr:
        if self.op == "id":
            return Value(self.args[0].val)

    def __str__(self) -> str:
        return f"{self.op} #{self.args[0]}"
