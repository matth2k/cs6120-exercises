import z3
import lark
import argparse

GRAMMAR = """
?start: term
  | term "?" term ":" term -> if

?term: item
  | term "*"  item      -> mul
  | item "(" term ")"      -> mul
  | term "/"  item      -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl
  | term "+" item        -> add
  | term "-" item        -> sub
  | "(" term ")" "^" index -> exp

?item: var
  | const
  | var "[" index "]" -> onebit
  | var "[" index ":" index "]" -> bitsel
  | "(" start ")"
  | var "^" index -> pow
  | const item -> multiple

?var: CNAME -> var

?const: NUMBER           -> num
  | "-" item            -> neg

?index: NUMBER           -> index

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()

rootBitVecSize = 16


def interp(tree, lookup):
    """Evaluate the arithmetic expression.

    Pass a tree as a Lark `Tree` object for the parsed expression. For
    `lookup`, provide a function for mapping variable names to values.
    """

    op = tree.data
    if op in (
        "add",
        "sub",
        "mul",
        "div",
        "shl",
        "shr",
        "multiple",
    ):  # Binary operators.
        lhs = interp(tree.children[0], lookup)
        rhs = interp(tree.children[1], lookup)
        if op == "add":
            return lhs + rhs
        elif op == "sub":
            return lhs - rhs
        elif op == "mul" or op == "multiple":
            return lhs * rhs
        elif op == "div":
            return lhs / rhs
        elif op == "shl":
            return lhs << rhs
        elif op == "shr":
            return lhs >> rhs
    elif op == "neg":  # Negation.
        sub = interp(tree.children[0], lookup)
        return -sub
    elif op == "num":  # Literal number.
        return z3.BitVecVal(int(tree.children[0]), rootBitVecSize)
    elif op == "index":  # Literal number.
        return int(tree.children[0])
    elif op == "var":  # Variable lookup.
        return lookup(tree.children[0])
    elif op == "if":  # Conditional.
        cond = interp(tree.children[0], lookup)
        true = interp(tree.children[1], lookup)
        false = interp(tree.children[2], lookup)
        return (cond != z3.BitVecVal(0, cond.size())) * true + (
            cond == z3.BitVecVal(0, cond.size())
        ) * false
    elif op == "onebit":
        sub = interp(tree.children[0], lookup)
        idx = interp(tree.children[1], lookup)
        if idx >= sub.size() or idx < 0:
            raise ValueError("Index out of bounds")
        return (sub & z3.BitVecVal(pow(2, idx), sub.size())) >> z3.BitVecVal(
            idx, sub.size()
        )
    elif op == "bitsel":
        sub = interp(tree.children[0], lookup)
        hi = interp(tree.children[1], lookup)
        lo = interp(tree.children[2], lookup)
        if hi >= sub.size() or hi < 0:
            raise ValueError("Hi index out of bounds")
        if lo >= sub.size() or lo < 0:
            raise ValueError("Lo index out of bounds")
        if hi < lo:
            raise ValueError("Hi index must be greater than lo index")
        power = hi - lo + 1
        mask = z3.BitVecVal(pow(2, power) - 1, sub.size()) << z3.BitVecVal(
            lo, sub.size()
        )
        return (sub & mask) >> z3.BitVecVal(lo, sub.size())
    elif op == "pow" or op == "exp":
        sub = interp(tree.children[0], lookup)
        exp = interp(tree.children[1], lookup)
        if exp < 1:
            raise ValueError("bad exponent")
        newExpr = sub
        for i in range(exp - 1):
            newExpr = newExpr * sub
        return newExpr


def pretty(tree, subst={}, paren=False):
    """Pretty-print a tree, with optional substitutions applied.

    If `paren` is true, then loose-binding expressions are
    parenthesized. We simplify boolean expressions "on the fly."
    """

    # Add parentheses?
    if paren:

        def par(s):
            return "({})".format(s)

    else:

        def par(s):
            return s

    op = tree.data
    if op in ("add", "sub", "mul", "div", "shl", "shr", "pow", "exp", "multiple"):
        lhs = pretty(tree.children[0], subst, True)
        rhs = pretty(tree.children[1], subst, True)
        c = {
            "add": "+",
            "sub": "-",
            "mul": "*",
            "multiple": " ",
            "div": "/",
            "shl": "<<",
            "shr": ">>",
            "pow": "^",
            "exp": "^",
        }[op]
        if op == "pow" or op == "exp":
            return par("{}{}{}".format(lhs, c, rhs))
        if op == "multiple":
            return par("{}{}".format(lhs, rhs))
        return par("{} {} {}".format(lhs, c, rhs))
    elif op == "neg":
        sub = pretty(tree.children[0], subst)
        return "-{}".format(sub, True)
    elif op == "num" or op == "index":
        return tree.children[0]
    elif op == "var":
        name = tree.children[0]
        return str(subst.get(name, name))
    elif op == "if":
        cond = pretty(tree.children[0], subst)
        true = pretty(tree.children[1], subst)
        false = pretty(tree.children[2], subst)
        return par("{} ? {} : {}".format(cond, true, false))
    elif op == "onebit":
        sub = pretty(tree.children[0], subst)
        idx = pretty(tree.children[1], subst)
        return par("{}[{}]".format(sub, idx))
    elif op == "bitsel":
        sub = pretty(tree.children[0], subst)
        hi = pretty(tree.children[1], subst)
        lo = pretty(tree.children[2], subst)
        return par("{}[{}:{}]".format(sub, hi, lo))


def solve(phi):
    s = z3.Solver()
    s.add(phi)
    s.check()  # The formula can be satisfied
    return s.model()


def vanishes(phi):
    s = z3.Solver()
    s.add(phi)
    try:
        s.check()  # The formula can be satisfied
        # print(s.model())
        return s.model()
    except:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This program uses an SMT solver to determine if a univariate expression is polynomial in 'x' and zero modulo 8"
    )
    parser.add_argument(
        "-v", "--verbose", dest="verbose", default=False, action="store_true"
    )
    parser.add_argument(
        "-N",
        "--bits",
        dest="bits",
        type=int,
        default="16",
        help="The number of bits the input variable 'x' is",
    )
    parser.add_argument(
        "expression", type=str, default="x", help="The expression p(x) to check"
    )
    args = parser.parse_args()
    rootBitVecSize = args.bits
    # Parse a polynomial.
    parser = lark.Lark(GRAMMAR)
    tree1 = parser.parse(args.expression)
    expr = interp(tree1, lambda x: z3.BitVec(x, rootBitVecSize) if x in ["x"] else None)
    print("Expression entered:")
    print(pretty(tree1))

    # Vars needed
    x = z3.BitVec("x", rootBitVecSize)
    # Holes
    A = z3.BitVec("A", rootBitVecSize)
    B = z3.BitVec("B", rootBitVecSize)
    C = z3.BitVec("C", rootBitVecSize)
    D = z3.BitVec("D", rootBitVecSize)
    E = z3.BitVec("E", rootBitVecSize)
    # Ax(x-1)(x-2)(x-3) + 4Bx(x-1)(x-2) + 4Cx(x-1) + 8Dx + 8E
    polynomial = (
        (A * x * (x - 1) * (x - 2) * (x - 3))
        + (4 * B * x * (x - 1) * (x - 2))
        + (4 * C * x * (x - 1))
        + (8 * D * x)
        + (8 * E)
    )

    formula = z3.ForAll([x], expr == polynomial)
    print("Q: Is this expression polynomial in 'x' and zero modulo 8?")
    answer = vanishes(formula)
    if answer is None:
        print("A: No")
    else:
        print("A: Yes it is, with vanishing polynomial")
        VExpr = ""
        if answer[A].as_long() != 0:
            if len(VExpr) > 0:
                VExpr += " + "
            VExpr += f"{answer[A].as_long()}x(x-1)(x-2)(x-3)"
        if answer[B].as_long() != 0:
            if len(VExpr) > 0:
                VExpr += " + "
            VExpr += f"{4 * answer[B].as_long()}x(x-1)(x-2)"
        if answer[C].as_long() != 0:
            if len(VExpr) > 0:
                VExpr += " + "
            VExpr += f"{4 * answer[C].as_long()}x(x-1)"
        if answer[D].as_long() != 0:
            if len(VExpr) > 0:
                VExpr += " + "
            VExpr += f"{8 * answer[D].as_long()}x"
        print(VExpr if len(VExpr) > 0 else "0")
