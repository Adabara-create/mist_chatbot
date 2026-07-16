import sympy
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def solve_math(expression: str) -> str:
    """Solve an arithmetic/algebraic expression or equation exactly.
    Uses sympy instead of the LLM because precise computation is a solved
    problem a library should own — an LLM can misfire on arithmetic."""
    try:
        if "=" in expression and "==" not in expression:
            lhs_raw, rhs_raw = expression.split("=", 1)
            lhs = parse_expr(lhs_raw, transformations=_TRANSFORMATIONS)
            rhs = parse_expr(rhs_raw, transformations=_TRANSFORMATIONS)
            symbols = sorted(lhs.free_symbols | rhs.free_symbols, key=str)
            if not symbols:
                return str(lhs == rhs)
            solutions = sympy.solve(sympy.Eq(lhs, rhs), symbols)
            return str(solutions)

        expr = parse_expr(expression, transformations=_TRANSFORMATIONS)
        simplified = sympy.simplify(expr)
        try:
            return str(simplified.evalf())
        except Exception:
            return str(simplified)
    except Exception as e:
        return f"Could not solve that expression: {e}"
