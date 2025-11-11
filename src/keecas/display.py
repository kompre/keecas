"""Display functions for LaTeX rendering

This module provides functions for rendering LaTeX equations in Jupyter notebooks using IPython.display.Markdown.

"""

from __future__ import annotations

import re
from collections.abc import Callable
from itertools import zip_longest
from typing import Any, Literal
from warnings import warn

import regex
from IPython.display import Latex
from sympy import (
    Basic,
    Le,
    latex,
)

from .col_wrappers import wrap_column
from .config.manager import get_config_manager
from .dataframe import Dataframe, create_dataframe
from .localization import translate

# Use the unified configuration system
config = get_config_manager().options

# Template choice type for IDE autocomplete
TemplateChoice = Literal["default", "boxed", "minimal"]

# ============================================================================
# PUBLIC API - Main Display Functions
# ============================================================================


def show_eqn(
    eqns: dict[Any, Any] | list[dict[Any, Any]] | Dataframe,
    environment: str | dict[str, Any] | None = None,
    sep: str | list[str] | None = None,
    label: str | dict[str, str | Callable] | Callable | None = None,
    label_command: str | None = None,
    col_wrap: str | dict | list | Dataframe | Callable | None = None,
    float_format: str | dict | list | Dataframe | None = None,
    cell_formatter: Callable | dict | list | Dataframe | None = None,
    row_formatter: Callable | dict | None = None,
    debug: bool | None = None,
    print_label: bool | None = None,
    katex: bool | None = None,
    env_arg: str | None = None,
    **kwargs: Any,
) -> Latex:
    r"""Display mathematical equations as formatted LaTeX amsmath block.

    Converts Python dictionaries containing symbolic expressions into rendered LaTeX
    equations suitable for Jupyter notebooks and Quarto documents. Supports multi-column
    layouts, custom formatting, labeling, and various LaTeX environments.

    Args:
        eqns: Equation data as dict, list of dicts, or Dataframe object.
            Automatically converted to Dataframe internally. For list of dicts: first
            dict's keys become Dataframe keys, subsequent dicts add columns where keys
            match (None for mismatches). See Dataframe.__init__ for details.
        environment: LaTeX environment name or custom definition. Built-in environments include
            "align", "equation", "cases", "gather", "split", "alignat", "rcases". Can also be
            a dict or EnvironmentDefinition object for custom environments.
            Defaults to config.latex.default_environment.
        sep: Separator(s) between cells in the amsmath block (e.g. `LHS & RHS & ...`).
            Can be string or list of strings for finer customization (separator goes
            between columns: first separator between columns 1-2, etc). Defaults to
            environment's default separator (None uses environment default: "&" for
            align, "" for equation/gather).
        label: Label(s) for cross-referencing equations. Can be:
            - str: Single label string (pre-formatted with generate_label)
            - dict: Mapping symbols to label strings or callables
            - Callable: Function that generates labels, receives single list: [key] + Dataframe[key]
            Labels should be pre-formatted using generate_label() before passing to show_eqn.
            Callable labels receive a single list argument: [key, value1, value2, ...].
            Omitted in KaTeX mode for notebook compatibility.
        label_command: LaTeX label command (e.g., r"\label"). Defaults to config.latex.default_label_command.
        col_wrap: Column wrapping specifications for LaTeX formatting.
            Can be str, dict, list, Dataframe, or Callable. For lists, the last element
            automatically fills remaining columns. Supports tuple values for prefix/suffix:
            [None, ("=", ""), (r"\\quad(", ")")] works correctly.
            List elements: None (no wrapping), str (prefix only), tuple (prefix, suffix),
            or Callable. Defaults to config.display.col_wrap.
        float_format: Format specification for float values (does not affect int).
            Can be str (all floats), list of str (per column), dict (per row), dict of
            list or Dataframe (per cell). For lists, the last element automatically fills
            remaining columns. Example: [None, ".3f", ".2f"] means col 0: no format,
            col 1: ".3f", col 2+: ".2f". Supports format specs with or without braces
            (e.g., ".3f" or "{:.3f}"). Defaults to config.display.default_float_format.
        cell_formatter: Custom cell value formatter function(s).
            Can be single Callable[(value, col_index) -> str] (all cells), list of
            Callable (per column), dict of Callable (per row if key matches), dict of
            list of Callable or Dataframe (per cell). For lists, the last element
            automatically fills remaining columns.
            Defaults to config.display.cell_formatter.
        row_formatter: Custom row-level formatter function(s).
            Can be single Callable[(row_latex_str) -> str] or dict mapping symbol keys
            to formatters. Applies to the composed entire row (str). Defaults to
            config.display.row_formatter.
        debug: Enable debug mode to print generated LaTeX source code. Defaults to config.display.debug.
        print_label: Print labels to console for easy copy-paste reference. Defaults to config.display.print_label.
        katex: Enable KaTeX compatibility mode (disables label commands). Defaults to config.display.katex.
        env_arg: Optional environment argument (e.g., "{2}" for alignat{2}). User provides complete
            argument string including braces.
        **kwargs: Additional keyword arguments:
            - language (str): Document-level language override for translations
            - substitutions (dict): Custom translation dictionary (highest priority)
            - Other sympy.latex() parameters (e.g., mul_symbol, fold_frac_powers)

    Returns:
        IPython.display.Latex object containing rendered LaTeX equations

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Basic parameter display with subscripted symbols
        F, A_load = symbols(r"F, A_{load}")

        _p = {
            F: 100*u.kN,
            A_load: 20*u.cm**2
        }

        show_eqn(_p)
        ```

        ```{python}
        # Multi-column with expressions and values
        sigma_Sd = symbols(r"\sigma_{Sd}")

        _e = {
            sigma_Sd: "F/A_load" | pc.parse_expr
        }

        _v = {k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}

        show_eqn([_p|_e, _v])
        ```

        ```{python}
        # Custom formatting and labels

        from keecas import config

        config.display.print_label = True

        # label dictionary
        _l = {
            F: 'force',
            A_load: 'area',
            sigma_Sd: 'stress-calc',
        }

        # specific float formatting
        _f = {
            F: '{:.1f}', # applied to all element in the row
            A_load: '{:.2f}', # applied to all element in the row
            sigma_Sd: [None, None, '.3f'], # per cell formatting
        }

        show_eqn([_p|_e, _v], float_format=_f, label=_l)
        ```

        ```{python}
        # Custom formatting and description

        from keecas import config

        config.display.print_label = True

        # short description
        _d = {
            F: 'applied force',
            A_load: 'area of application',
            sigma_Sd: 'stress',
        }

        # use hash function to create unique labels
        _l = {k: hash(v) for k,v in _d.items()}

        show_eqn(
            [_p|_e, _v, _d],
            float_format=['', '.2f', '.4f'],
            # float_format='.2f',
            label=_l
        )
        ```

        ```{python}
        # Different environments
        from IPython.display import display

        # tip: if show_eqn used mid-cell, use display() to emit rendered output to notebook
        display(show_eqn(_p, environment="align"))  # aligned at '=' sign
        show_eqn(_p, environment="gather")    # Centered, no alignment
        ```

        ```{python}
        # Custom environment with parentheses
        custom_env = {
            "separator": "&",
            "line_separator": r" \\ ",
            "supports_multiple_labels": True,
            "outer_environment": "align",
            "inner_environment": "aligned",
            "inner_prefix": r"\left(",
            "inner_suffix": r"\right)",
        }
        show_eqn([_e, _v], environment=custom_env)
        ```

        ```{python}
        # Custom environment for one-line display
        one_line_env = {
            "separator": " ",
            "line_separator": r";\quad ",
            "supports_multiple_labels": False,
            "outer_environment": "equation",
        }
        show_eqn([_p|_e, _v], environment=one_line_env)
        ```

    See Also:
        - `~~display.check`: Engineering verification with localization
        - `~~utils.dict_to_eq`: Convert dict to SymPy Eq objects
        - `~~utils.eq_to_dict`: Convert SymPy Eq objects to dict
        - `~~config.manager.ConfigManager`: Global configuration object

    Notes:
        - LaTeX output respects config.katex setting (disables labels for KaTeX compatibility)
        - Float formatting supports format specs with or without braces: ".3f" or "{:.3f}"
        - Environment separator defaults to None (uses environment-specific default)
        - Labels use config.latex.eq_prefix and eq_suffix for consistent referencing
        - use config.display.print_label=True to display resulting label to be used for referencing (it will display the label even in KaTeX mode)
    """

    # set default values
    if debug is None:
        debug = config.display.debug

    if print_label is None:
        print_label = config.display.print_label

    if katex is None:
        katex = config.display.katex

    # Use config default_float_format if not explicitly provided
    if float_format is None:
        float_format = config.display.default_float_format

    # Prepare latex kwargs for formatters (validate and set defaults)
    from keecas.formatters import validate_latex_kwargs

    # Filter out localization parameters that shouldn't go to latex()
    latex_kwargs = {k: v for k, v in kwargs.items() if k not in ["language", "substitutions"]}

    # Set default mul_symbol if not provided
    if "mul_symbol" not in latex_kwargs:
        latex_kwargs["mul_symbol"] = config.latex.default_mul_symbol

    # Validate latex kwargs
    latex_kwargs = validate_latex_kwargs(latex_kwargs)

    # Handle inline environment definitions
    from keecas.config.manager import EnvironmentDefinition

    if isinstance(environment, dict):
        # Convert dict to EnvironmentDefinition
        env_config = EnvironmentDefinition.from_dict(environment)
        environment = "custom_inline"  # Use generic name for template generation
    elif isinstance(environment, EnvironmentDefinition):
        # Use EnvironmentDefinition directly
        env_config = environment
        environment = "custom_inline"
    else:
        # String environment name - look up in config
        if not environment:
            environment = config.latex.default_environment

        env_config = config.latex.environments.get(environment.replace("*", ""))
        if not env_config:
            warn(f"Unknown environment '{environment}', using 'align'")
            env_config = config.latex.environments.align
            environment = "align"

    if col_wrap is None:
        col_wrap = config.display.col_wrap if config.display.col_wrap is not None else wrap_column

    # warning message in case of too many labels provided
    if not env_config.supports_multiple_labels and isinstance(label, dict):
        warn(
            f"ATTENTION! label is a dict, while the {environment} does not support multiple labels",
        )

    # Use environment separator if not explicitly provided
    if sep is None:
        sep = env_config.separator

    # convert sep to a list: str-> list[str]
    if not isinstance(sep, list):
        sep = [sep]

    # convert eqns to a Dataframe
    if not isinstance(eqns, Dataframe):
        if isinstance(eqns, list):
            eqns = Dataframe(eqns)
        else:
            eqns = Dataframe([eqns])

    # adjust sep to the size of the list of eqns(e.g. 'key & val0 & val1' ); assume last value of sep as filler
    sep += [sep[-1]] * (eqns.width - len(sep))

    # extract keys from first dict
    keys = eqns.keys()
    # determine the number of columns (keys & value0 & value1 ...)
    num_cols = eqns.width + 1

    ### create float_format Dataframe
    # Extract seed and filler using last-element pattern
    float_format_seed, float_format_filler = _extract_seed_and_filler(float_format)
    float_format = create_dataframe(
        float_format_seed,
        keys,
        num_cols,
        default_value=float_format_filler,
    )

    ### col_wrap
    # Extract seed and filler using last-element pattern
    col_wrap_seed, col_wrap_filler = _extract_seed_and_filler(col_wrap)
    col_wrap = create_dataframe(
        col_wrap_seed,
        keys,
        num_cols,
        default_value=col_wrap_filler,
    )

    ### cell_formatter
    # Import default formatter
    from keecas.formatters import format_value

    # Step 1: Determine default if not provided
    if cell_formatter is None:
        cell_formatter = config.display.cell_formatter or format_value

    # Step 2: Extract seed and filler using last-element pattern
    cell_formatter_seed, cell_formatter_filler = _extract_seed_and_filler(cell_formatter)
    # Use format_value as fallback if no filler provided
    if cell_formatter_filler is None:
        cell_formatter_filler = format_value

    cell_formatters = create_dataframe(
        cell_formatter_seed,
        keys,
        num_cols,
        default_value=cell_formatter_filler,
    )

    # get the config default label (it could be None), or generate label dict if none is passed
    if not label:
        label = config.latex.label or {k: None for k in keys}

    # define label command
    if not label_command:
        label_command = config.latex.default_label_command

    # Generate template using environment configuration
    first_key = list(keys)[0] if keys else None
    template = _generate_environment_template(
        environment,
        env_config,
        label,
        first_key,
        label_command,
        env_arg,
        print_label,
        katex,
    )

    # generate the rows
    body_lines = {}
    for key, list_values in eqns.items():
        # Generate cells with custom formatters
        cells = []
        for col_idx, (v, s, cw, ff, cf) in enumerate(
            zip_longest(
                ([key] + list_values),
                sep,
                col_wrap[key],
                float_format[key],
                cell_formatters[key],  # Add to zip_longest
                fillvalue="",
            ),
        ):
            # Apply formatter with column index and latex kwargs
            if v is not None:
                formatted_value = cf(v, col_idx, **latex_kwargs)  # Pass latex kwargs to formatter
                # Note: formatted_value is never None - registry ensures fallback
                cell_content = f"{_col_wrap(cw, v, col_idx)[0]}{formatted_value}{_col_wrap(cw, v, col_idx)[-1]}"
            else:
                cell_content = " "

            # Apply float formatting
            cell_content = format_decimal_numbers(f"{cell_content} {s}", ff)
            cells.append(cell_content)

        # Join cells to form row
        body_lines[key] = " ".join(cells) + _attach_label(
            label, key, label_command, list_values, print_label, katex
        )

    # Apply row-level formatters
    if row_formatter is not None:
        if callable(row_formatter):
            # Single function for all rows
            body_lines = {k: row_formatter(v) for k, v in body_lines.items()}
        elif isinstance(row_formatter, dict):
            # Key-specific row formatters (dict keys = symbol keys)
            body_lines = {k: row_formatter.get(k, lambda x: x)(v) for k, v in body_lines.items()}
    elif config.display.row_formatter is not None:
        # Use config default if available
        row_func = config.display.row_formatter
        body_lines = {k: row_func(v) for k, v in body_lines.items()}

    # Use line separator from environment config
    join_token = env_config.line_separator

    # generate the body
    body = join_token.join(body_lines.values())

    # clean the body
    body = _replace_all(
        body,
        language=kwargs.get("language"),
        substitutions=kwargs.get("substitutions"),
    )

    template = template.replace("___body___", body)

    if debug:
        print(template)

    return Latex(template)


def check(
    lhs: int | float,
    rhs: int | float,
    test: type = Le,
    template: TemplateChoice | None = None,
    success_template: str | None = None,
    failure_template: str | None = None,
    **kwargs: Any,
) -> Latex:
    r"""Engineering verification function with localized pass/fail indicators.

    Compares two expressions (already evaluated to numeric values) using a test function and displays a formatted
    message based on the pass/fail status. Return message can be templated as Latex object. The most common case is to be passed to a show_eqn function as secondary dict (the object will be formatted according to `cell_formatter` specification).

    NOTE: if the test cannot evaluate to either True or False, an error will be raised. Common cause for this is that one of the arguments passed are not in the numeric form, but still in symbolic form.

    Args:
        lhs: evaluated left-hand side expression (e.g., calculated stress or utilization ratio).
        rhs: evaluated right-hand side expression (e.g., allowable limit or capacity).
        test: Comparison function from SymPy's relational module. Options:
            - Le: LessThan (default, less than or equal)
            - Ge: GreaterThan (greater than or equal)
            - Lt: StrictLessThan (strictly less than)
            - Gt: StrictGreaterThan (strictly greater than)
            - Eq: Equality
            - Ne: Unequality
            Defaults to Le (less than or equal to).
        template: Named template set for formatting. Options: "default", "boxed", "minimal".
            Controls visual presentation of verification result.
        success_template: Custom template string for passing checks. Available variables:
            {symbol}, {rhs}, {verified_text}, {color}, {test_result}, {result_text}.
        failure_template: Custom template string for failing checks. Same variables as success_template.
        **kwargs: Additional keyword arguments:
            - language (str): Document-level language override (e.g., 'it', 'de', 'fr')
            - substitutions (dict): Custom translation dictionary for "VERIFIED"/"NOT_VERIFIED"

    Returns:
        IPython.display.Latex object that depends on conditions (true or false).

    Examples:
        ```{python}
        from keecas import symbols, u, pc, check
        from sympy import Le, Ge

        # Basic utilization check (calculated <= allowable)
        sigma_Sd, sigma_Rd = symbols(r"\sigma_{Sd}, \sigma_{Rd}")
        _p = {sigma_Sd: 150*u.MPa, sigma_Rd: 200*u.MPa}

        utilization = sigma_Sd / sigma_Rd | pc.subs(_p) | pc.N
        check(utilization, 1.0, test=Le)  # Check if <= 1.0 (passes)
        ```

        ```{python}
        from keecas import show_eqn

        # Capacity check (demand <= capacity)
        N_Ed, N_Rd = symbols(r"N_{Ed}, N_{Rd}")
        _p = {N_Ed: 850*u.kN, N_Rd: 1200*u.kN}

        _e = {
            k: k | pc.subs(_p) | pc.N for k in [N_Ed/N_Rd]
        }

        _c = {
            k: check(v, 1.0) for k, v in _e.items()
        }

        # use along show_eqn
        show_eqn([_p | _e, _c])
        ```

        ```{python}
        # Multiple checks with different tests
        tau_Sd, tau_Rd = symbols(r"\tau_{Sd}, \tau_{Rd}")
        _v = {tau_Sd: 45*u.MPa, tau_Rd: 50*u.MPa}

        # Check shear stress is less than limit
        check(
            tau_Sd | pc.subs(_v) | pc.N,
            tau_Rd | pc.subs(_v) | pc.N,
            test=Le
        )
        ```

        ```{python}
        # Check capacity is greater than demand (reverse comparison)
        check(
            tau_Rd | pc.subs(_v) | pc.N,
            tau_Sd | pc.subs(_v) | pc.N,
            test=Ge
        )
        ```

        ```{python}
        # Localized verification (Italian)
        from keecas import config
        config.language.language = 'it'

        utilization = 0.75
        check(utilization, 1.0, test=Le)  # Shows "VERIFICATO" in Italian
        ```

        ```{python}
        # Custom templates for different visual styles
        from IPython.display import display

        # tip: use display() to show output for mid-cell statements
        display(check(0.85, 1.0, template="boxed") )   # Boxed result
        display(check(0.85, 1.0, template="minimal") ) # Minimal formatting
        check(0.85, 1.0, template="default")  # Standard formatting
        ```

    See Also:
        - `~~display.show_eqn`: Display mathematical equations
        - `~~config.manager.ConfigManager`: Global configuration for language and formatting
        - `~~localization.translate`: Low-level translation function

    Notes:
        - Returns green indicator for passing checks, red for failing (default template)
        - Verification text ("VERIFIED"/"NOT_VERIFIED") automatically localized per config.language
        - Supports 10 languages: de, es, fr, it, pt, da, nl, no, sv, en
        - Template variables allow full customization of output format
        - Commonly used with utilization ratios: check(calculated/allowable, 1.0)
        - Test functions from SymPy: Le, Ge, Lt, Gt, Eq, Ne
    """
    # Determine comparison symbols based on test type
    match test.__name__:
        case "LessThan":
            symbol_if_true = r"\le"
            symbol_if_false = r">"
        case "StrictLessThan":
            symbol_if_true = r"<"
            symbol_if_false = r"\ge"
        case "GreaterThan":
            symbol_if_true = r"\ge"
            symbol_if_false = r"<"
        case "StrictGreaterThan":
            symbol_if_true = r">"
            symbol_if_false = r"\le"
        case "Equality":
            symbol_if_true = r"="
            symbol_if_false = r"\neq"
        case "Unequality":
            symbol_if_true = r"\neq"
            symbol_if_false = r"="

    # Extract template parameters (explicit args take precedence over kwargs for backward compatibility)
    template_name = template or kwargs.get("template")
    success_template_param = success_template or kwargs.get("success_template")
    failure_template_param = failure_template or kwargs.get("failure_template")
    language = kwargs.get("language")
    substitutions = kwargs.get("substitutions")

    # Get templates
    templates = _get_check_templates(
        template_name,
        success_template_param,
        failure_template_param,
    )

    # Get localized verification text
    verified_text = translate(
        "VERIFIED",
        language=language,
        substitutions=substitutions,
    )
    not_verified_text = translate(
        "NOT_VERIFIED",
        language=language,
        substitutions=substitutions,
    )

    # Perform the test
    test_result = test(lhs, rhs)

    # Select template and symbol based on result
    if test_result:
        template_str = templates["success"]
        symbol = symbol_if_true
        color = "green"
        result_text = verified_text
    else:
        template_str = templates["failure"]
        symbol = symbol_if_false
        color = "red"
        result_text = not_verified_text

    # Format template with variables
    formatted_result = _format_check_template(
        template_str,
        symbol=symbol,
        rhs=latex(rhs),
        verified_text=verified_text,
        not_verified_text=not_verified_text,
        color=color,
        test_result=test_result,
        result_text=result_text,
    )

    return Latex(formatted_result)


# ============================================================================
# PUBLIC API - Utility Functions
# ============================================================================


def format_decimal_numbers(
    text: str | None,
    format_string: str | None = None,
) -> str | None:
    r"""Format all decimal numbers in a LaTeX string with specified precision.

    Searches for decimal numbers in LaTeX strings and applies Python format
    specifications to control precision and display. Used internally by
    show_eqn() for cell-level formatting but available for custom LaTeX
    string manipulation.

    NOTE: Only matches standard decimal notation (e.g., "1.234", "-0.567").
    Does not match scientific notation or integers without decimal points.

    Args:
        text: LaTeX string containing decimal numbers to format. If None,
            returns None unchanged.
        format_string: Python format specification for float formatting.
            Supports flexible notation:
            - ".3f" (shorthand, common usage)
            - "{:.3f}" (full format string)
            - ":0.3f" (with zero-padding)
            If None, returns text unchanged. Defaults to None.

    Returns:
        LaTeX string with all decimal numbers formatted according to
        format_string, or None if text is None.

    Raises:
        ValueError: If format_string is invalid or cannot format floats.

    Examples:
        ```{python}
        from keecas.display import format_decimal_numbers

        # Basic usage with shorthand notation
        latex = r"\sigma_{Sd} = 1.23456 \text{ MPa}"
        formatted = format_decimal_numbers(latex, ".2f")
        print(formatted)
        ```

        ```{python}
        # Multiple decimal numbers in one string
        latex = r"F = 100.567 \text{ kN}, A_{load} = 20.123 \text{ cm}^2"
        formatted = format_decimal_numbers(latex, ".1f")
        print(formatted)
        ```

        ```{python}
        # Different format specifications
        latex = r"\alpha_{max} = 3.14159"

        # Standard precision
        print(format_decimal_numbers(latex, ".3f"))

        # Scientific notation
        print(format_decimal_numbers(latex, ".2e"))

        # Zero-padding
        print(format_decimal_numbers(latex, "06.2f"))
        ```

        ```{python}
        # Integration with show_eqn workflow
        from keecas import symbols, u, show_eqn
        from sympy import latex

        # tip: use for custom post-processing of LaTeX strings
        sigma_Rd = symbols(r"\sigma_{Rd}")
        value_latex = latex(5.123456 * u.MPa)

        # Format specific parts before display
        formatted_latex = format_decimal_numbers(value_latex, ".2f")
        print(formatted_latex)
        ```

    See Also:
        - `~~display.show_eqn`: Main display function with built-in float formatting
        - `~~config.manager.DisplayConfig`: Display configuration (see `default_float_format` attribute)

    Notes:
        - Only matches decimal numbers (requires decimal point)
        - Negative numbers supported (matches leading minus sign)
        - Format string automatically normalized from shorthand to full format
        - Returns None unchanged if either text or format_string is None
        - Used internally by show_eqn() for per-cell formatting
        - Regex pattern: r"-?\d+\.\d+" (matches standard decimal notation)
    """
    if text is None or format_string is None:
        return text

    # Normalize format string: handle shorthand notation
    normalized_format = format_string
    if not normalized_format.startswith("{"):
        # Handle common cases
        if normalized_format.startswith(":"):
            # User provided ":0.3f" -> "{:0.3f}"
            normalized_format = "{" + normalized_format + "}"
        else:
            # User provided ".3f" -> "{:.3f}"
            normalized_format = "{:" + normalized_format + "}"

    # Validate by attempting to format a test value
    try:
        _ = normalized_format.format(1.0)
    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid float_format '{format_string}': {e}")

    def _format_match(match):
        value = float(match.group())
        return normalized_format.format(value)

    return re.sub(r"-?\d+\.\d+", _format_match, text)


def latex_inline_dict(var: Basic, mapping: dict[Basic, Any], **kwargs: Any) -> str:
    """Generate inline LaTeX equation from a variable and its value in a mapping.

    Creates a formatted LaTeX string showing "var = value" where both the
    variable and value are rendered as LaTeX. Supports different modes for
    wrapping the output (plain, inline math, or environment).

    Args:
        var: SymPy symbol to display on left-hand side
        mapping: Dictionary containing the value for the variable
        **kwargs: Additional arguments passed to sympy.latex()
            - mode: Output mode - "plain" (default), "inline" (with $...$),
                    or environment name (with \\begin{}...\\end{})
            - mul_symbol: Multiplication symbol (default: "\\,")
            - Other sympy.latex() parameters

    Returns:
        Formatted LaTeX string with localization applied

    Examples:
        ```{python}
        from keecas import symbols
        from keecas.display import latex_inline_dict

        # Define symbol with subscript
        sigma_Sd = symbols(r"\\sigma_{Sd}")

        # Basic usage
        latex_inline_dict(sigma_Sd, {sigma_Sd: 5})  # Returns: '\\sigma_{Sd} = 5'
        ```

        ```{python}
        # Inline mode with $ delimiters
        latex_inline_dict(sigma_Sd, {sigma_Sd: 5}, mode="inline")  # Returns: '$\\sigma_{Sd} = 5$'
        ```

    See Also:
        - `~~display.show_eqn`: Main display function for multiple equations
        - `~~utils.dict_to_eq`: Convert dictionary to SymPy Eq objects
    """
    if "mul_symbol" not in kwargs:
        kwargs["mul_symbol"] = r"\,"
    match mode := kwargs.get("mode"):
        case "plain" | None:
            wrap = ("", "")
        case "inline":
            wrap = ("$", "$")
        case _:
            wrap = (rf"\begin{{{mode}}}", rf"\end{{{mode}}}")

    kwargs["mode"] = "plain"

    def _latex(x):
        return _replace_all(latex(x, **kwargs))

    return f"{wrap[0]}{_latex(var)} = {_latex(mapping[var])}{wrap[1]}"


# ============================================================================
# PRIVATE HELPERS - Text Replacement and Localization
# ============================================================================


def _replace_all(
    body: str,
    reps: dict[str, str | callable] | None = None,
    language: str | None = None,
    substitutions: dict[str, str] | None = None,
) -> str:
    """
    Replace patterns in body text using localization-aware replacements.

    Args:
        body: Text to process
        reps: Custom replacement dictionary (overrides default)
        language: Document-level language override (if None, uses global language settings)
        substitutions: Direct substitution dictionary

    Returns:
        Processed text with replacements applied
    """
    if reps is None:
        reps = _get_replacement_dict(language=language, substitutions=substitutions)

    for pattern, repl in reps.items():
        body = regex.sub(pattern, repl, body)
    return body


def _get_replacement_dict(
    language: str | None = None,
    substitutions: dict[str, str] | None = None,
) -> dict[str, str | callable]:
    """
    Get complete replacement dictionary combining base and localized replacements.

    Args:
        language: Document-level language override (if None, uses global language settings)
        substitutions: Direct substitution dictionary

    Returns:
        Complete replacement dictionary for regex processing
    """
    replacements = _get_base_replacements()
    replacements.update(_get_localized_replacements(language, substitutions))
    return replacements


def _get_localized_replacements(
    language: str | None = None,
    substitutions: dict[str, str] | None = None,
) -> dict[str, str]:
    """Get localized replacements based on current language settings."""
    return {
        r"\bfor\b": translate("for", language=language, substitutions=substitutions),
        r"\botherwise\b": translate(
            "otherwise",
            language=language,
            substitutions=substitutions,
        ),
        # Domain/Range labels from SymPy LaTeX output (match \text{...} patterns)
        r"\\text\{Domain: \}": f"\\text{{{translate('Domain: ', language=language, substitutions=substitutions)}}}",
        r"\\text\{Domain on \}": f"\\text{{{translate('Domain on ', language=language, substitutions=substitutions)}}}",
        r"\\text\{Range\}": f"\\text{{{translate('Range', language=language, substitutions=substitutions)}}}",
    }


def _get_base_replacements() -> dict[str, str | callable]:
    """Get non-localizable replacements that are always applied."""
    return {
        r"\\frac": r"\\dfrac",  # first replace all frac with dfrac
        r"\^\{((?:[^{}]|(?:\{(?1)\}))*)}": lambda m: regex.sub(
            "dfrac",
            "frac",
            m.group(0),
        ),  # then replace all dfrac inside ^{} with frac (small exponent)
        r"\b1 \\cdot": r"",
        r"\\\\": rf"\\\\[{config.latex.vertical_skip}]",
        r"\\,": r"{\,}",
    }


# ============================================================================
# PRIVATE HELPERS - Formatting and Template Generation
# ============================================================================


def _extract_seed_and_filler(value: Any) -> tuple[Any, Any]:
    """Extract seed and filler from various input formats.

    For list inputs, the last element serves as the filler value that will be
    used to pad remaining columns. For non-list inputs, no filler is extracted.

    Args:
        value: Input value (scalar, list, dict, Dataframe)

    Returns:
        (seed, filler) tuple where:
        - seed: Value to pass to create_dataframe
        - filler: Value to use as default_value in create_dataframe

    Examples:
        >>> _extract_seed_and_filler([".1f", ".2f"])
        ([".1f", ".2f"], ".2f")

        >>> _extract_seed_and_filler(".3f")
        (".3f", None)

        >>> _extract_seed_and_filler([".3f"])
        ([".3f"], ".3f")
    """
    if isinstance(value, list) and len(value) > 0:
        # Last element is filler
        return value, value[-1]
    else:
        # Scalar, empty list, dict, or Dataframe - no list filler
        return value, None


def _col_wrap(
    cw: None | str | tuple[str, str] | dict[type, tuple[str, str]] | Callable,
    value: Any,
    col_index: int = 0,
) -> tuple[str, str]:
    """Apply column wrapping based on wrapper specification.

    Parameters
    ----------
    cw : None | str | tuple | dict | Callable
        Column wrapper specification
    value : Any
        Value being wrapped
    col_index : int, optional
        Column index (0 = LHS, 1+ = RHS)

    Returns
    -------
    tuple[str, str]
        (prefix, suffix) for wrapping
    """
    if not cw:
        return ("", "")

    if callable(cw):
        return cw(value, col_index)

    if isinstance(cw, str):
        return cw, ""

    if isinstance(cw, tuple):
        return cw

    if isinstance(cw, dict):
        for type, col_wraps in cw.items():
            if isinstance(value, type):
                return col_wraps

    return ("", "")


def _attach_label(
    label: str | dict[str, str] | Callable[[list[Any]], str] | None,
    key: str | None = None,
    label_command: str | None = None,
    values: list[Any] | None = None,
    print_label: bool = False,
    katex: bool = False,
) -> str:
    r"""Attach a label to a given key.

    Args:
        label: The label or label dictionary. Can be:
            - str: Single label string (pre-formatted)
            - dict: Dictionary mapping keys to label strings or callables
            - Callable: Function to generate label (receives single list: [key] + values)
        key: The key to attach the label to, or None for single labels
        label_command: LaTeX label command (e.g., r"\label")
        values: List of values for this row (used with callable labels)
        print_label: Whether to print labels to console for debugging
        katex: Whether to omit labels for KaTeX compatibility

    Returns:
        LaTeX label command string, or empty string if no label or KaTeX mode

    Notes:
        - Labels should be pre-formatted using generate_label() before passing to show_eqn
        - If print_label is True, the key and label are printed for debugging
        - Labels are omitted in KaTeX mode for Jupyter notebook compatibility
        - Callable labels receive a single list argument: [key] + values
    """
    if not label_command:
        label_command = config.latex.default_label_command

    # Handle callable label (single callable for all keys)
    if callable(label) and key is not None:
        text_label = label([key] + values)
        if print_label:
            print(f"{key}: {text_label}") if text_label else None

        return rf" {label_command}{{{text_label}}} " if text_label and not katex else ""

    if isinstance(label, dict):
        label_value = label.get(key)

        # Handle callable value in dict
        if callable(label_value):
            text_label = label_value([key] + values)
        elif label_value:
            text_label = label_value
        else:
            text_label = ""

        if print_label:
            print(f"{key}: {text_label}") if text_label else None

        return rf" {label_command}{{{text_label}}} " if text_label and not katex else ""

    if isinstance(label, str) and not key:
        text_label = label

        if print_label:
            print(f"label: {text_label}" if text_label else None)

        return rf" {label_command}{{{text_label}}} " if not katex else ""

    return ""


def _generate_environment_template(
    environment: str,
    env_config,
    label: str | dict[str, str] | None,
    first_key: str | None = None,
    label_command: str | None = None,
    env_arg: str | None = None,
    print_label: bool = False,
    katex: bool = False,
) -> str:
    """Generate complete LaTeX template with ___body___ placeholder.

    Args:
        environment: Environment name (may include '*' for starred variant)
        env_config: EnvironmentDefinition object
        label: Label string or label dictionary
        first_key: First key for single-label environments
        label_command: LaTeX label command
        env_arg: Optional argument string for environment (e.g., "{2}" for alignat{2}).
                 User provides complete argument including braces.
        print_label: Whether to print labels to console for debugging
        katex: Whether to omit labels for KaTeX compatibility

    Returns:
        LaTeX template string with ___body___ placeholder
    """
    outer_env = env_config.outer_environment
    inner_env = env_config.inner_environment

    # Handle starred environments
    if "*" in environment:
        outer_env += "*"

    # Use env_arg directly (already includes braces) or empty string
    arg_str = env_arg if env_arg else ""

    if inner_env is None:
        # Standard environment: \begin{env}{arg}___body___\end{env}
        outer_prefix = env_config.outer_prefix
        outer_suffix = env_config.outer_suffix

        # Single label environments attach label to begin statement
        label_str = (
            _attach_label(label, first_key, label_command, None, print_label, katex)
            if not env_config.supports_multiple_labels
            else ""
        )

        template = (
            rf"{outer_prefix}\begin{{{outer_env}}}{arg_str}{label_str}"
            + "\n___body___\n"
            + rf"\end{{{outer_env}}}{outer_suffix}"
        )
    else:
        # Nested environment: \begin{outer}\n\t\prefix\begin{inner}{arg}___body___\end{inner}\suffix\n\end{outer}
        # Argument goes on inner environment by default
        inner_prefix = env_config.inner_prefix
        inner_suffix = env_config.inner_suffix
        outer_prefix = env_config.outer_prefix
        outer_suffix = env_config.outer_suffix

        # Label goes on outer environment for nested structures
        label_str = _attach_label(label, None, label_command, None, print_label, katex)

        template = rf"""{outer_prefix}\begin{{{outer_env}}}{label_str}
	{inner_prefix}\begin{{{inner_env}}}{arg_str}
___body___
	\end{{{inner_env}}}{inner_suffix}
\end{{{outer_env}}}{outer_suffix}"""

    return template


def _get_check_templates(
    template_name: str | None = None,
    success_override: str | None = None,
    failure_override: str | None = None,
) -> dict[str, str]:
    """Get check templates from config or overrides."""
    # Use overrides if provided
    if success_override and failure_override:
        return {"success": success_override, "failure": failure_override}

    # Use named template set if specified
    if template_name and template_name in config.check_templates.template_sets:
        template_set = config.check_templates.template_sets[template_name]
        return {"success": template_set["success"], "failure": template_set["failure"]}

    # Fall back to default config templates
    return {
        "success": config.check_templates.success_template,
        "failure": config.check_templates.failure_template,
    }


def _format_check_template(template: str, **variables: Any) -> str:
    """Format template string with variable substitution."""
    try:
        return template.format(**variables)
    except KeyError as e:
        # If template is missing required variables, fall back to default
        warn(f"Template missing variable {e}, using default template")
        default_template = (
            config.check_templates.success_template
            if variables.get("test_result")
            else config.check_templates.failure_template
        )
        return default_template.format(**variables)
