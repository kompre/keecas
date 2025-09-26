# Keecas Cell Templates
# Copy and paste these templates into Jupyter notebook cells

# =============================================================================
# NOTEBOOK SETUP (Run once per notebook)
# =============================================================================

# Imports
from keecas import symbols, u, pc, show_eqn, options, check

# Configuration (optional)
# options.katex = True              # For KaTeX compatibility
# options.PRINT_LABEL = True        # Print labels in dev mode
# options.EQ_PREFIX = r"eq-PREFIX-" # Label prefixing

# Global persistence dicts
params = {}  # Global parameters that persist across cells
eqn = {}     # Global expressions that persist across cells

# =============================================================================
# BASIC CELL PATTERN (Cell-local only)
# =============================================================================

# Define symbols
symbol1, symbol2, result = symbols("symbol1, symbol2, result")

# Parameters with units
_p = {
    symbol1: value1 * u.unit1,
    symbol2: value2 * u.unit2,
}

# Symbolic expressions
_e = {
    result: "symbol1 * symbol2" | pc.parse_expr
}

# Evaluation
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.target_unit]) | pc.N
    for k, v in _e.items()
}

# Display
show_eqn([_p | _e, _v])

# =============================================================================
# PERSISTENT CELL PATTERN (With notebook-global storage)
# =============================================================================

# Define symbols
symbol1, symbol2, result = symbols("symbol1, symbol2, result")

# Parameters (cell-local, then persist)
_p = {
    symbol1: value1 * u.unit1,
    symbol2: value2 * u.unit2,
}
params.update(_p)  # Save to global params

# Expressions (cell-local, then persist)
_e = {
    result: "symbol1 * symbol2" | pc.parse_expr
}
eqn.update(_e)  # Save to global expressions

# Evaluation (using both cell-local and global)
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.target_unit]) | pc.N
    for k, v in _e.items()
}

# Display
show_eqn([_p | _e, _v])

# =============================================================================
# FULL FEATURED CELL PATTERN (All keecas features)
# =============================================================================

# Define symbols
symbol1, symbol2, result = symbols("symbol1, symbol2, result")

# Parameters
_p = {
    symbol1: value1 * u.unit1,
    symbol2: value2 * u.unit2,
}
params.update(_p)  # Persist if needed

# Expressions
_e = {
    result: "symbol1 * symbol2" | pc.parse_expr
}
eqn.update(_e)  # Persist if needed

# Evaluation
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.target_unit]) | pc.N
    for k, v in _e.items()
}

# Descriptions
_d = {
    symbol1: "description of symbol1",
    symbol2: "description of symbol2",
    result: "description of result"
}

# Labels (for cross-referencing)
_l = {k: str(k) for k in _e.keys()}

# Verification checks
_c = {k: check(v, 1.0) for k, v in _v.items()}

# Float formatting
_ff = {k: "{:.3f}" for k in _v.keys()}

# Display with all features
show_eqn([_p | _e, _v, _d, _c],
         label=_l,
         float_format=_ff,
         col_wrap=[None, "=", "=", (r"\quad(", ")"), "&"])

# =============================================================================
# VERIFICATION PATTERNS
# =============================================================================

# Simple verification
_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]
_v = {k: k | pc.subs(_e | _p) | pc.N for k in _expr}
_c = {k: check(v, 1.0) for k, v in _v.items()}
show_eqn([_v, _c])

# Complex verification with test specifications
from sympy import Le, Lt, Ge, Gt, Eq

_expr = {
    a: (3, Le, 1),    # 3 ≤ 1
    b: (4, Gt, 2),    # 4 > 2
    c: (5, Lt, 3),    # 5 < 3
}
_c = {k: check(lhs=v[0], test=v[1], rhs=v[2]) for k, v in _expr.items()}
show_eqn([{k: v[0] for k, v in _expr.items()}, _c])

# =============================================================================
# ENVIRONMENT-SPECIFIC PATTERNS
# =============================================================================

# Cases environment
_p = {param1: value1, param2: value2}
_d = {param1: "description1", param2: "description2"}
show_eqn([_p, _d],
         environment="cases",
         col_wrap=[None, "=", "&"])

# Equation environment with labels
_e = {result: "expression" | pc.parse_expr}
_v = {k: v | pc.subs(_e | _p) | pc.N for k, v in _e.items()}
_l = {k: str(k) for k in _e.keys()}
show_eqn([_e, _v],
         environment="equation",
         label=_l,
         float_format="{:.3f}")

# =============================================================================
# DATAFRAME PATTERN
# =============================================================================

from keecas import Dataframe

# Create dataframe
data = Dataframe({
    'Case': ['Case1', 'Case2', 'Case3'],
    'Value': [1*u.kN, 2*u.kN, 3*u.kN],
    'Factor': [1.0, 1.5, 2.0]
})

# Add computed column
_v = {case: val * factor for case, val, factor in zip(data['Case'], data['Value'], data['Factor'])}
data['Result'] = list(_v.values())

show_eqn(data.to_dict())

# =============================================================================
# SYMBOL DEPENDENCY ORDERING (Automatic)
# =============================================================================

# Define expressions that reference each other
# Keecas automatically handles dependency ordering
_e = {
    final_result: "intermediate1 + intermediate2" | pc.parse_expr,
    intermediate1: "a * b" | pc.parse_expr,
    intermediate2: "c / d" | pc.parse_expr,
}

_v = {
    k: v | pc.subs(eqn | params) | pc.N
    for k, v in _e.items()
}

show_eqn([_e, _v])