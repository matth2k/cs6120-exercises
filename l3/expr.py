from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
import sys


def get_first_live(dict: dict[Any, bool]) -> Any:
    for k, v in dict.items():
        if v:
            return k
    return None


class Expr(ABC):
    @abstractmethod
    def fold(self, num2Val: dict[Value, Expr] = None) -> Expr:
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

    def to_instr(
        self, oldInsn, var2Num: dict[str, Expr], num2Val: dict[Value, tuple[Expr, Any]]
    ) -> Any:
        dest = oldInsn["dest"] if "dest" in oldInsn else None
        oldArgs = oldInsn["args"] if "args" in oldInsn else None
        if isinstance(self, Const):
            return {"op": "const", "dest": dest, "value": self.val, "type": self.type}
        elif isinstance(self, Value):
            return {
                "op": "id",
                "dest": dest,
                "type": self.type,
                "args": [
                    get_first_live(num2Val[self.val][1])
                    if self.val in num2Val
                    else oldArgs[0]
                ],
            }
        elif isinstance(self, BinaryExpr) or isinstance(self, UnaryExpr):
            return {
                "op": self.op,
                "dest": dest,
                "args": [get_first_live(num2Val[arg][1]) for arg in self.args],
                "type": self.type,
            }
        raise Exception(f"Unhandled Expression {self}")

    def from_instr(
        instr: Any,
        var2Num: dict[str, Expr] = None,
        num2Val: dict[Value, tuple[Expr, Any]] = None,
    ) -> Expr:
        if "dest" not in instr:
            return None
        if instr["op"] == "const":
            return Const(instr["value"], instr["type"])

        if var2Num is not None:
            if "args" in instr:
                for arg in instr["args"]:
                    if arg not in var2Num:
                        return None

        if instr["op"] in BinaryExpr.binary_ops:
            return BinaryExpr(
                instr["op"],
                tuple(
                    arg if var2Num is None else var2Num[arg] for arg in instr["args"]
                ),
                instr["type"],
            ).fold(num2Val)
        if instr["op"] in UnaryExpr.unary_ops:
            return UnaryExpr(
                instr["op"],
                tuple(
                    arg if var2Num is None else var2Num[arg] for arg in instr["args"]
                ),
                instr["type"],
            ).fold(num2Val)

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

    def fold(self, num2Val: dict[Value, tuple[Expr, Any]] = None) -> Expr:
        if self.op in self.commutative_ops and self.type != "float":
            newArgs = list(self.args).sort()
            if newArgs is not None:
                toTuple = tuple(newArgs)
                if toTuple != self.args:
                    return BinaryExpr(self.op, toTuple, self.type).fold(num2Val)

        constOperands = []
        if num2Val is not None:
            for arg in self.args:
                if arg in num2Val:
                    val = num2Val[arg][0].fold(num2Val)
                    if isinstance(val, Const):
                        constOperands.append(eval(f"{val.type}({val.val})"))
        if len(constOperands) == 2:
            computed = self.binary_ops[self.op](constOperands[0], constOperands[1])
            return Const(eval(f"{self.type}({computed})"), self.type)
        elif int(0) in constOperands and self.op == "mul":
            return Const(int(0), self.type)
        elif False in constOperands and self.op == "and":
            return Const(False, self.type)
        elif True in constOperands and self.op == "or":
            return Const(True, self.type)

        return BinaryExpr(self.op, self.args, self.type)

    def __str__(self) -> str:
        return f"{self.op} {self.args[0]}, {self.args[1]}"


class Value(Expr):
    def __init__(self, val: Any, type: str):
        self.val = val
        self.type = type

    def fold(self, num2Val: dict[Value, tuple[Expr, Any]] = None) -> Expr:
        return Value(self.val, self.type)

    def __lt__(self, obj):
        return self.val < obj.val

    def __str__(self) -> str:
        return f"#{self.val}"


class Const(Expr):
    def __init__(self, val: Any, type: str):
        self.val = val
        self.type = type

    def fold(self, num2Val: dict[Value, tuple[Expr, Any]] = None) -> Expr:
        return Const(self.val, self.type)

    def __lt__(self, obj):
        return self.val < obj.val

    def __str__(self) -> str:
        return f"const {self.val} : {self.type}"


class UnaryExpr(Expr):
    unary_ops = {"not": lambda a: not a, "id": lambda a: a}

    def __init__(self, op, arg: Any, type: str):
        self.op = op
        self.args = tuple(arg)
        self.type = type

    def fold(self, num2Val: dict[Value, tuple[Expr, Any]] = None) -> Expr:
        if self.op == "id":
            return Value(self.args[0].val, self.type).fold(num2Val)

        constOperands = []
        if num2Val is not None:
            for arg in self.args:
                if arg in num2Val:
                    val = num2Val[arg][0].fold(num2Val)
                    if isinstance(val, Const):
                        constOperands.append(eval(f"{val.type}({val.val})"))

        if len(constOperands) == 1:
            computed = self.unary_ops[self.op](constOperands[0])
            return Const(eval(f"{self.type}({computed})"), self.type)

    def __str__(self) -> str:
        return f"{self.op} {self.args[0]}"
