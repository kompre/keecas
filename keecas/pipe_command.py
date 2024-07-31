# %% pipe command
from pipe import Pipe
from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
from sympy import Basic, sympify
from sympy.physics.units.util import convert_to as sympy_convert_to
from sympy.physics.units.util import quantity_simplify as sympy_quantity_simplify
from sympy import topological_sort, default_sort_key
from itertools import permutations
from inspect import currentframe


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
def subs(expression: Basic, substitution: dict, sorted=True, quantity_simplify=True, **kwargs) -> Basic:
    
    # filter out non Basic expressions from the substitution dict
    substitution = {lhs: rhs for lhs, rhs in substitution.items() if isinstance(lhs, Basic)}
    
    if sorted:
        substitution = order_subs(substitution)
    
    expression = expression.subs(substitution)
           
    if quantity_simplify:        
        expression = expression | quantity_simplify(**kwargs)
        
    return 

@Pipe
def N(expression: Basic, precision: int = 15) -> Basic:
    return expression.evalf(precision) 

@Pipe
def convert_to(expression: Basic, units = 1) -> Basic:
    return sympy_convert_to(expression, target_units=units)

@Pipe
def doit(expression: Basic) -> Basic:
    return expression.doit()

@Pipe
def parse_expr(expression: Basic, evaluate=False, local_dict:dict=None, **kwargs) -> Basic:
    if not local_dict:
        local_dict = currentframe().f_back.f_back.f_back.f_locals
    
    parsed_expr = sympy_parse_expr(
        expression,
        evaluate=evaluate, 
        transformations="all",
        local_dict=local_dict, 
        **kwargs
    )
    return parsed_expr

@Pipe
def quantity_simplify(expression: Basic, across_dimensions=True, unit_system="SI", **kwargs) -> Basic:
    return sympy_quantity_simplify(expression, across_dimensions=across_dimensions, unit_system=unit_system)

# print(currentframe().f_back.f_locals)
# %% debug

if __name__ == '__main__':
    import sympy as sp
    
    x, y = sp.symbols('x y')
    
    _d = {
        x : 3,
        y : x*4, 
    }
    
    print("x*y" | parse_expr | subs(_d) | N | convert_to)
# %%
