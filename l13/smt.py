import z3
import lark

GRAMMAR = """
?start: sum
  | sum "?" sum ":" sum -> if

?sum: term
  | sum "+" term        -> add
  | sum "-" term        -> sub

?term: item
  | term "*"  item      -> mul
  | term "/"  item      -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl

?item: var
  | const
  | var "[" const "]" -> index
  | var "[" const ":" const "]" -> bitsel
  | "(" start ")"

?var: CNAME -> var

?const: NUMBER           -> num
  | "-" item            -> neg

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()


def interp(tree, lookup):
    """Evaluate the arithmetic expression.

    Pass a tree as a Lark `Tree` object for the parsed expression. For
    `lookup`, provide a function for mapping variable names to values.
    """

    op = tree.data
    if op in ("add", "sub", "mul", "div", "shl", "shr"):  # Binary operators.
        lhs = interp(tree.children[0], lookup)
        rhs = interp(tree.children[1], lookup)
        if op == "add":
            return lhs + rhs
        elif op == "sub":
            return lhs - rhs
        elif op == "mul":
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
        return int(tree.children[0])
    elif op == "var":  # Variable lookup.
        return lookup(tree.children[0])
    elif op == "if":  # Conditional.
        cond = interp(tree.children[0], lookup)
        true = interp(tree.children[1], lookup)
        false = interp(tree.children[2], lookup)
        return (cond != 0) * true + (cond == 0) * false
    elif op == "index":
        sub = interp(tree.children[0], lookup)
        idx = interp(tree.children[1], lookup)
        return (sub & z3.BitVecVal(pow(2, idx), sub.size())) >> z3.BitVecVal(
            idx, sub.size()
        )
    elif op == "bitsel":
        sub = interp(tree.children[0], lookup)
        hi = interp(tree.children[1], lookup)
        lo = interp(tree.children[2], lookup)
        power = hi - lo + 1
        mask = z3.BitVecVal(pow(2, power) - 1, sub.size()) << z3.BitVecVal(
            lo, sub.size()
        )
        return (sub & mask) >> z3.BitVecVal(lo, sub.size())


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
    if op in ("add", "sub", "mul", "div", "shl", "shr"):
        lhs = pretty(tree.children[0], subst, True)
        rhs = pretty(tree.children[1], subst, True)
        c = {
            "add": "+",
            "sub": "-",
            "mul": "*",
            "div": "/",
            "shl": "<<",
            "shr": ">>",
        }[op]
        return par("{} {} {}".format(lhs, c, rhs))
    elif op == "neg":
        sub = pretty(tree.children[0], subst)
        return "-{}".format(sub, True)
    elif op == "num":
        return tree.children[0]
    elif op == "var":
        name = tree.children[0]
        return str(subst.get(name, name))
    elif op == "if":
        cond = pretty(tree.children[0], subst)
        true = pretty(tree.children[1], subst)
        false = pretty(tree.children[2], subst)
        return par("{} ? {} : {}".format(cond, true, false))
    elif op == "index":
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


if __name__ == "__main__":
    # We know x times 2 is equivalent to a logical shify by?
    # x = z3.BitVec("x", 8)
    # a = z3.BitVecVal(10, 32)
    # print(a)
    # slow_expr = x * 2
    # hole = z3.BitVec("hole", 8)
    # fast_expr = x << hole

    # formula = z3.ForAll([x], fast_expr == slow_expr)
    # print(solve(formula))

    parser = lark.Lark(GRAMMAR)
    tree1 = parser.parse("(5 * (3 << x[3:1])) + y - 1")

    print(pretty(tree1))

    print(interp(tree1, lambda v: z3.BitVec(v, 32)))
