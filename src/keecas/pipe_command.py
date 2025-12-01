"""Pipe commands for functional composition of mathematical operations.

This module provides @Pipe decorated functions that enable chain operations
like: expr | pc.subs(vals) | pc.convert_to(units) | pc.N

All functions are designed to work with SymPy expressions and support
functional programming patterns for mathematical computation workflows.
"""

from inspect import currentframe
from itertools import permutations
from typing import Any

from pipe import Pipe
from sympy import (
    Basic,
    MatrixBase,
    Mul,
    S,
    UnevaluatedExpr,
    default_sort_key,
    sympify,
    topological_sort,
)
from sympy.core.function import UndefinedFunction
from sympy.parsing.sympy_parser import T
from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
from sympy.physics.units.util import convert_to as sympy_convert_to
from sympy.physics.units.util import quantity_simplify as sympy_quantity_simplify


def order_subs(subs: dict[Basic, Any]) -> list[tuple[Basic, Any]]:
    """Reorder substitutions using topological order for dependency resolution.

    Ensures that substitutions are applied in the correct order when variables
    depend on each other (e.g., y depends on x, so x must be substituted first).

    Args:
        subs: Dictionary of substitutions where keys are variables and values are expressions

    Returns:
        Ordered list of substitution tuples for exhaustive application
    """

    # Generate edges between each vertex
    edges = [(i, j) for i, j in permutations(subs.items(), 2) if sympify(i[1]).has(j[0])]

    # Reorder the dict with topological_sort
    return topological_sort((subs.items(), edges), default_sort_key)


@Pipe
def subs(
    expression: Basic,
    substitution: dict[Basic, Any],
    sorted: bool = True,
    # simplify_quantity=True, **kwargs
) -> Basic:
    r"""Substitute variables in symbolic expressions with values or other expressions.

    Applies substitutions to SymPy expressions while handling dependencies between
    variables. Commonly used in workflows to evaluate symbolic equations with
    parameters from `_p` dicts or intermediate expressions from `_e` dicts.
    Integrates with pipe operations for functional composition.

    NOTE: Returns None if input expression is None, allowing chain operations
    to gracefully handle missing values.

    Args:
        expression: SymPy expression to apply substitutions to. Can be any symbolic
            expression containing variables to be replaced.
        substitution: Dictionary mapping variables (symbols) to their replacement values
            (numeric values, quantities with units, or other expressions). Non-Basic
            keys and None values are automatically filtered out.
        sorted: Whether to apply topological sorting for dependency resolution.
            When True (default), automatically orders substitutions so that dependent
            variables are substituted in correct order (e.g., if y depends on x,
            x is substituted first). Defaults to True.

    Returns:
        SymPy expression with substitutions applied, or None if input is None.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Basic parameter substitution
        F, A_load = symbols(r"F, A_{load}")

        _p = {
            F: 100*u.kN,
            A_load: 20*u.cm**2,
        }

        sigma = symbols(r"\sigma")
        _e = {
            sigma: "F / A_load" | pc.parse_expr,
        }

        # Substitute parameters into expression
        result = _e[sigma] | pc.subs(_p)
        ```

        ```{python}
        # Multi-step workflow with merged dicts
        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Dependency resolution with sorted=True
        x, y, z = symbols(r"x, y, z")

        # y depends on x, z depends on y
        _e = {
            z: "x + y" | pc.parse_expr,
            y: "2 * x" | pc.parse_expr,
            x: 5,
        }

        # Automatic ordering: x first, then y, then z
        result = z | pc.subs(_e)  # sorted=True by default
        ```

    Notes:
        - Automatically filters out None values and non-Basic keys from substitution dict
        - Topological sorting handles complex dependency chains automatically
        - Works seamlessly with Pint quantities through SymPy integration
        - Common pattern: `_p | _e` merges parameters and expressions for substitution
    """
    # Filter out None expressions
    if expression is None:
        return None

    # Filter out non-Basic expressions from substitution dict
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
    r"""Numerically evaluate symbolic expressions to floating-point values.

    Converts symbolic expressions containing irrational numbers, constants, or
    unevaluated operations into numeric approximations. Commonly used as final
    step in calculation workflows before display with show_eqn().

    Args:
        expression: SymPy expression to evaluate numerically. Can contain symbolic
            math operations, constants (pi, e, etc.), or quantities with units.
        precision: Number of decimal digits for evaluation. Controls internal
            calculation precision, not display formatting (use float_format in
            show_eqn for display). Defaults to 15.

    Returns:
        Numerically evaluated SymPy expression as floating-point approximation.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn
        from sympy import pi

        # Basic numeric evaluation
        r = symbols(r"r")
        A_circle = symbols(r"A_{circle}")

        _p = {
            r: 5*u.cm,
        }

        _e = {
            A_circle: "pi * r**2" | pc.parse_expr,
        }

        # Evaluate symbolic pi to numeric value
        _v = {
            k: v | pc.subs(_p | _e) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Control precision for high-accuracy calculations
        import sympy as sp

        expr = sp.sqrt(2)

        # Default precision (15 digits)
        result_default = expr | pc.N

        # High precision (50 digits)
        result_high = expr | pc.N(precision=50)
        ```

        ```{python}
        # Typical workflow: subs -> convert_to -> N
        F, A_load, sigma_Sd = symbols(r"F, A_{load}, \sigma_{Sd}")

        _p = {
            F: 850*u.kN,
            A_load: 120*u.cm**2,
        }

        _e = {
            sigma_Sd: "F / A_load" | pc.parse_expr,
        }

        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

    Notes:
        - Precision parameter controls internal calculation accuracy, not display
        - For display formatting, use float_format parameter in show_eqn()
        - Works with Pint quantities, preserving units in output
        - Commonly chained after subs() and convert_to() in evaluation workflows
    """
    return expression.evalf(precision)


@Pipe
def convert_to(expression: Basic, units: Any = 1) -> Basic:
    r"""Convert quantities to different units while preserving values.

    Converts SymPy expressions with units to target units, handling both
    prefixed units (kN, daN, cm) and compound units (MPa, kN/m). Commonly
    used in engineering workflows to standardize units before display or
    comparison. Integrates seamlessly with Pint unit definitions.

    Args:
        expression: SymPy expression with units to convert. Must contain
            dimensional quantities (e.g., force, pressure, length).
        units: Target units for conversion. Can be:
            - Single unit (e.g., u.MPa)
            - List of units (e.g., [u.kN, u.mm])
            - Compound units (e.g., u.kN/u.m)
            Defaults to 1 (dimensionless).

    Returns:
        Expression converted to target units with same magnitude in new units.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Basic unit conversion
        F, A_load = symbols(r"F, A_{load}")

        _p = {
            F: 5000*u.N,  # Newtons
            A_load: 120*u.cm**2,
        }

        # Convert to kilonewtons
        _v = {
            F: _p[F] | pc.convert_to(u.kN),
            A_load: _p[A_load] | pc.convert_to(u.m),
        }

        show_eqn([_p, _v])
        ```

        ```{python}
        # Compound unit conversion
        sigma = symbols(r"\sigma")

        _p = {
            F: 850*u.kN,
            A_load: 120*u.cm**2,
        }

        _e = {
            sigma: "F / A_load" | pc.parse_expr,
        }

        # Convert pressure to MPa
        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to(u.MPa) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # List of target units for flexibility
        L, delta = symbols(r"L, \delta")

        _p = {
            L: 8*u.m,
        }

        _e = {
            delta: "L / 400" | pc.parse_expr,
        }

        # Try converting to mm, fallback to other units if needed
        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to([u.mm]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

    Notes:
        - Prefixed units (kN, cm, MPa) handled automatically via SymPy prefix system
        - Non-prefixed units (kgf, lbf) use scale factors from Pint definitions
        - All Pint units convert correctly through SymPy integration
        - Commonly chained between subs() and N() in evaluation workflows
        - List of units allows flexible conversion with fallback options
    """
    return sympy_convert_to(expression, target_units=units)


@Pipe
def doit(expression: Basic) -> Basic:
    r"""Evaluate unevaluated operations in symbolic expressions.

    Forces evaluation of operations that SymPy keeps in symbolic form, such as
    derivatives, integrals, summations, or limits. Useful when symbolic operations
    need numeric results or simplified forms.

    Args:
        expression: SymPy expression containing unevaluated operations (derivatives,
            integrals, summations, limits, etc.) that should be evaluated.

    Returns:
        Expression with all unevaluated operations evaluated to their results.

    Examples:
        ```{python}
        from keecas import symbols, pc
        import sympy as sp

        # Evaluate derivative
        x = symbols(r"x")
        expr = sp.Derivative(x**2, x)

        # Without doit: shows Derivative(x**2, x)
        print(expr)

        # With doit: evaluates to 2*x
        result = expr | pc.doit
        print(result)
        ```

        ```{python}
        # Evaluate integral
        integral_expr = sp.Integral(sp.sin(x), x)

        # Evaluates to -cos(x)
        result = integral_expr | pc.doit
        ```

        ```{python}
        # Use in calculation workflow
        from keecas import u, show_eqn

        F, x_coord = symbols(r"F, x")

        _p = {
            F: 100*u.kN,
        }

        # Expression with derivative
        _e = {
            symbols(r"dF/dx"): sp.Derivative(F * x_coord**2, x_coord),
        }

        # Evaluate derivative then substitute
        _v = {
            k: v | pc.doit | pc.subs(_p) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

    Notes:
        - Works with derivatives, integrals, limits, summations, and products
        - May be needed before subs() to properly substitute into evaluated forms
        - Not all operations can be evaluated symbolically (may return unchanged)
        - Combines well with other pipe commands in calculation workflows
    """
    return expression.doit()


@Pipe
def parse_expr(
    expression: str,
    local_dict: dict[str, Any] | None = None,
    evaluate: bool = False,
    **kwargs: Any,
) -> Basic:
    r"""Parse mathematical expression strings into SymPy symbolic objects.

    Converts string representations of mathematical expressions into SymPy
    expressions that can be manipulated symbolically. Most commonly used with
    pipe operator to define expressions in `_e` dicts using readable string
    notation instead of verbose SymPy syntax.

    NOTE: Automatically captures local variables from caller's scope when
    local_dict is None, enabling clean string-based expression definitions.

    Args:
        expression: String representation of mathematical expression using standard
            notation (e.g., "F / A", "pi * r**2", "sqrt(x**2 + y**2)"). Supports
            operators: +, -, *, /, **, parentheses, and common functions.
        local_dict: Dictionary of local variables for parsing context (symbol
            definitions, parameters, functions). If None, automatically uses
            caller's local variables from enclosing scope. Defaults to None.
        evaluate: Whether to evaluate the expression during parsing (e.g., simplify
            numeric operations). When False, preserves structure as written.
            Defaults to False.
        **kwargs: Additional arguments passed to SymPy's parse_expr:
            - transformations: List of parsing transformations (defaults to T[:11])
            - global_dict: Global symbol dictionary
            - rational: Whether to convert floats to rationals

    Returns:
        Parsed SymPy expression object ready for symbolic manipulation.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Most common pattern: define expressions as strings
        F, A_load, sigma = symbols(r"F, A_{load}, \sigma")

        _p = {
            F: 100*u.kN,
            A_load: 20*u.cm**2,
        }

        # Use parse_expr to convert string to SymPy expression
        _e = {
            sigma: "F / A_load" | pc.parse_expr,
        }

        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Complex expressions with functions
        from sympy import pi

        r, A_circle, V_sphere = symbols(r"r, A_{circle}, V_{sphere}")

        _p = {
            r: 5*u.cm,
        }

        _e = {
            A_circle: "pi * r**2" | pc.parse_expr,
            V_sphere: "(4/3) * pi * r**3" | pc.parse_expr,
        }

        _v = {
            k: v | pc.subs(_p | _e) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Custom local_dict for additional functions
        from sympy import sqrt

        custom_locals = {
            'special_func': lambda x: sqrt(x**2 + 1),
        }

        expr = "special_func(5)" | pc.parse_expr(local_dict=custom_locals)
        ```

        ```{python}
        # Multiple dependent expressions
        x, y, z, result = symbols(r"x, y, z, result")

        _p = {
            x: 3,
            y: 4,
        }

        # Expressions can reference each other
        _e = {
            z: "sqrt(x**2 + y**2)" | pc.parse_expr,
            result: "z * 2" | pc.parse_expr,
        }

        # tip: automatic dependency resolution with pc.subs
        _v = {
            k: v | pc.subs(_p | _e) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

    Notes:
        - Uses transformations T[:11] by default for standard mathematical parsing
        - Automatically captures caller's local scope for symbol resolution
        - Common functions supported: sin, cos, sqrt, log, exp, abs, etc.
        - Operators: +, -, *, /, ** (power), parentheses for grouping
        - Cleaner than verbose SymPy syntax: "F/A" vs sp.Div(F, A)
        - Idiomatic pattern: define symbols, then use string expressions in _e dict
    """

    if not local_dict:
        frame = currentframe()
        # Frame stack: parse_expr (0) -> __ror__ (1) -> lambda (2) -> caller (3)
        frame3 = frame.f_back.f_back.f_back

        if not frame3:
            local_dict = {}
        else:
            # Python 3.13 compatibility: cross-module isolation via f_globals
            #
            # Always merge f_globals + f_locals to match Python's scoping:
            # - f_globals: bound to DEFINING module (not calling module)
            #   This ensures cross-module isolation - if module_b imports module_a
            #   and calls module_a.func(), we see module_a's globals, not module_b's
            # - f_locals: function-local variables and loop variables
            # - Precedence: f_locals override f_globals (locals shadow globals)
            #
            # This handles all common cases:
            # 1. Functions accessing module variables: ✓ (f_globals)
            # 2. Module-level comprehensions: ✓ (f_globals + loop vars)
            # 3. Cross-module isolation: ✓ (f_globals is defining module)
            #
            # Known limitation (Python 3.13 PEP 667):
            # - Comprehensions inside functions can't access parent function locals
            #   due to scope isolation. Workaround: pass explicit local_dict parameter
            local_dict = {**dict(frame3.f_globals), **dict(frame3.f_locals)}

    if "transformations" not in kwargs:
        kwargs["transformations"] = T[:11]

    parsed_expr = sympy_parse_expr(
        expression,
        evaluate=evaluate,
        local_dict=local_dict,
        **kwargs,
    )
    return parsed_expr


@Pipe
def quantity_simplify(
    expression: Basic,
    across_dimensions: bool = True,
    unit_system: str = "SI",
    **kwargs: Any,
) -> Basic:
    r"""Simplify expressions with units by combining and reducing quantities.

    Applies SymPy's quantity simplification to combine terms with compatible units
    and reduce complex unit expressions. Useful for cleaning up expressions with
    multiple unit terms or dimensional analysis.

    Args:
        expression: SymPy expression to simplify, typically containing multiple
            terms with units that can be combined or reduced.
        across_dimensions: Whether to simplify across different dimensions (e.g.,
            combine force and length into energy). When True, allows broader
            simplifications. Defaults to True.
        unit_system: Unit system for simplification, determines which base units
            to use. Options include "SI", "CGS", "imperial". Defaults to "SI".
        **kwargs: Additional arguments passed to SymPy's quantity_simplify:
            - across_dimensions: Override the across_dimensions parameter
            - unit_system: Override the unit_system parameter

    Returns:
        Simplified SymPy expression with combined and reduced unit terms.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Simplify expression with multiple force terms
        F_1, F_2, F_total = symbols(r"F_1, F_2, F_{total}")

        _p = {
            F_1: 100*u.kN,
            F_2: 50000*u.N,
        }

        _e = {
            F_total: "F_1 + F_2" | pc.parse_expr,
        }

        # Simplify combines terms with compatible units
        _v = {
            k: v | pc.subs(_p | _e) | pc.quantity_simplify | pc.convert_to([u.kN]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Dimensional analysis with unit simplification
        F, d, E = symbols(r"F, d, E")

        _p = {
            F: 500*u.N,
            d: 2*u.m,
        }

        # Work (energy) from force and distance
        _e = {
            E: "F * d" | pc.parse_expr,
        }

        # Simplify to base energy units
        _v = {
            k: v | pc.subs(_p | _e) | pc.quantity_simplify | pc.convert_to([u.J]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Different unit systems
        from sympy import sympify
        from sympy.physics.units import newton, kilonewton

        # Create expression with different unit prefixes
        expr = 100*kilonewton + 5000*newton

        # Simplify combines compatible units
        result = expr | pc.quantity_simplify(unit_system="SI")
        print(result)  # Combines to single unit
        ```

    Notes:
        - Combines terms with compatible units (e.g., kN + N -> kN)
        - Simplifies compound units to base units when appropriate
        - across_dimensions=True enables dimensional analysis simplifications
        - Works with both SI and other unit systems
        - May need convert_to() afterward to get desired output units
    """

    return sympy_quantity_simplify(
        expression,
        across_dimensions=across_dimensions,
        unit_system=unit_system,
    )


@Pipe
def as_two_terms(
    expression: Basic,
    as_mul: bool = False,
) -> Basic | tuple[Basic, Basic]:
    """Split expression into magnitude and units components.

    Separates multiplicative expressions or matrices into two terms,
    typically magnitude and units for cleaner display.

    Args:
        expression: SymPy expression to split
        as_mul: If True, return as unevaluated multiplication

    Returns:
        Two-term tuple or unevaluated multiplication, depending on as_mul.
        Returns original expression if splitting is not applicable.

    Notes:
        For matrices, splits only if all elements share the same units.
    """
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
def as_Mul(expression: tuple[Basic, Basic]) -> Basic:
    """Create unevaluated multiplication from tuple of expressions.

    Multiplies two expressions while keeping them visually separated,
    ideal for displaying magnitude and units distinctly.

    Args:
        expression: Tuple containing two SymPy expressions to multiply

    Returns:
        Unevaluated multiplication expression for clean display
    """

    return UnevaluatedExpr(expression[0]) * UnevaluatedExpr(expression[1])


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
