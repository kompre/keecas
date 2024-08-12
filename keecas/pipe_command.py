# %% pipe command
from pipe import Pipe
from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
from sympy import Basic, sympify, S, Mul, MatrixBase, UnevaluatedExpr
from sympy.core.function import UndefinedFunction
from sympy.physics.units.util import convert_to as sympy_convert_to
from sympy.physics.units.util import quantity_simplify as sympy_quantity_simplify
from sympy import topological_sort, default_sort_key
from itertools import permutations
from inspect import currentframe
from keecas.display import wrap_floats


def order_subs(subs: dict) -> list[tuple]:
    """Reorders the substitutions using topological order, ensuring that
    the order of elements passed to the subs function is exhaustive.

    Args:
        subs (dict): Dictionary of substitutions to perform (VERTICES).

    Returns:
        list: Ordered list of substitutions.
    """

    # Generate edges between each vertex
    edges = [
        (i, j) for i, j in permutations(subs.items(), 2) if sympify(i[1]).has(j[0])
    ]

    # Reorder the dict with topological_sort
    return topological_sort((subs.items(), edges), default_sort_key)


@Pipe
def subs(
    expression: Basic,
    substitution: dict,
    sorted=True,
    # simplify_quantity=True, **kwargs
) -> Basic:

    # filter out None expressions from the expression
    if expression is None:
        return

    # filter out non Basic expressions from the substitution dict
    substitution = {
        lhs: rhs
        for lhs, rhs in substitution.items()
        if isinstance(lhs, Basic | UndefinedFunction | str) and rhs is not None
    }

    if sorted:
        substitution = order_subs(substitution)

    expression = S(expression).subs(substitution)

    # if simplify_quantity:
    #     expression = expression | quantity_simplify(**kwargs)

    return expression


@Pipe
def N(expression: Basic, precision: int = 15) -> Basic:
    return expression.evalf(precision)


@Pipe
def convert_to(expression: Basic, units=1) -> Basic:
    return sympy_convert_to(expression, target_units=units)


@Pipe
def doit(expression: Basic) -> Basic:
    return expression.doit()


from sympy.parsing.sympy_parser import T


@Pipe
def parse_expr(
    expression: Basic, local_dict: dict = None, evaluate=False, **kwargs
) -> Basic:
    if not local_dict:
        local_dict = currentframe().f_back.f_back.f_back.f_locals

    if "transformations" not in kwargs:
        kwargs["transformations"] = T[:11]

    parsed_expr = sympy_parse_expr(
        expression, evaluate=evaluate, local_dict=local_dict, **kwargs
    )
    return parsed_expr


@Pipe
def quantity_simplify(
    expression: Basic, across_dimensions=True, unit_system="SI", **kwargs
) -> Basic:
    return sympy_quantity_simplify(
        expression, across_dimensions=across_dimensions, unit_system=unit_system
    )


@Pipe
def as_two_terms(
    expression: Basic,
    as_mul=False,
) -> Basic:
    if isinstance(expression, Mul):
        att = expression.as_two_terms()
    elif isinstance(expression, MatrixBase):
        units = {u for e in expression.values() for u in e.as_coefficients_dict()}
        if len(units) == 1:
            u = units.pop()
            att = (expression / u, u)
        else:
            return expression
    else:
        return expression

    return att | as_Mul if as_mul else att


@Pipe
def as_Mul(expression: tuple[Basic]) -> Basic:
    return UnevaluatedExpr(expression[0]) * expression[1]


# print(currentframe().f_back.f_locals)
# %% debug

if __name__ == "__main__":
    import sympy as sp

    x, y = sp.symbols("x y")

    _d = {
        x: 3,
        y: x * 4,
    }
    print((None) | subs(_d))

    e = sp.symbols("e", cls=sp.Function)
    _e = {e: "Lambda(j, j+1)" | parse_expr}
    print("e(x)" | parse_expr | subs(_e))

# %%
