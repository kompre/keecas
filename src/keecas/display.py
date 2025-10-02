# %%
from __future__ import annotations

from warnings import warn
from sympy import (
    latex,
    Eq,
    Le,
    symbols,
    Basic,
    FunctionClass,
    Dict,
    S,
)
from IPython.display import Markdown, display
import re

from pint import Quantity

from typing import Any, Literal

from .dataframe import *

# default values for labels
from dataclasses import dataclass

from .config import get_config_manager
from .localization import translate

# Use the unified configuration system
_config_manager = get_config_manager()
config = _config_manager.options


from itertools import chain, zip_longest


# Template choice type for IDE autocomplete
TemplateChoice = Literal["default", "boxed", "minimal"]


def _attach_label(
    label: str | dict[str, str] | None,
    key: str | None = None,
    label_command: str | None = None,
) -> str:
    r"""Attach a label to a given key.

    Args:
        label: The label or label dictionary
        key: The key to attach the label to, or None for single labels
        label_command: LaTeX label command (e.g., r"\label")

    Returns:
        LaTeX label command string, or empty string if no label or KaTeX mode

    Notes:
        - The label is constructed using config.latex.eq_prefix, label[key], and config.latex.eq_suffix
        - If config.display.print_label is True, the key and label are printed for debugging
        - Labels are omitted in KaTeX mode for Jupyter notebook compatibility
    """
    if not label_command:
        label_command = config.latex.default_label_command

    if isinstance(label, dict):
        text_label = (
            rf"{config.latex.eq_prefix}{label[key]}{config.latex.eq_suffix}"
            if label.get(key)
            else ""
        )
        if config.display.print_label:
            print(f"{key}: {text_label}") if text_label else None

        return (
            rf" {label_command}{{{text_label}}} "
            if label.get(key)
            and not config.display.katex  # don't add the label if there is no label to add, and if katex engine is used for rendering (i.e. jupyter notebook)
            else ""
        )

    if isinstance(label, str) and not key:

        text_label = rf"{config.latex.eq_prefix}{label}{config.latex.eq_suffix}"

        if config.display.print_label:
            print(f"label: {text_label}" if text_label else None)

        return (
            rf" {label_command}{{{text_label}}} "
            if not config.display.katex  # don't add the label if there is no label to add, and if katex engine is used for rendering (i.e. jupyter notebook)
            else ""
        )

    return ""


def _generate_environment_template(
    environment: str,
    env_config,
    label: str | dict[str, str] | None,
    first_key: str | None = None,
    label_command: str | None = None,
    env_arg: str | None = None,
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
            _attach_label(label, first_key, label_command)
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
        label_str = _attach_label(label, None, label_command)

        template = rf"""{outer_prefix}\begin{{{outer_env}}}{label_str}
	{inner_prefix}\begin{{{inner_env}}}{arg_str}
___body___
	\end{{{inner_env}}}{inner_suffix}
\end{{{outer_env}}}{outer_suffix}"""

    return template


# Template processing helpers for check function
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


# check verification result
def check(
    lhs: Basic,
    rhs: Basic,
    test=Le,
    template: TemplateChoice | None = None,
    success_template: str | None = None,
    failure_template: str | None = None,
    **kwargs: Any,
) -> Markdown:
    """Determines if the left-hand side (lhs) is less than or equal to
    the right-hand side (rhs) based on the provided test function.

    Args:
        lhs (sympy.Expr): The left-hand side expression.
        rhs (sympy.Expr): The right-hand side expression.
        test (sympy.GreaterThan, sympy.LessThan, sympy.GreaterThanEqual, sympy.LessThanEqual, optional):
            The test function to apply. Defaults to Le (less than or equal to).
        template (TemplateChoice, optional): Named template set to use ("default", "boxed", "minimal").
        success_template (str, optional): Custom success template override with variables like {symbol}, {rhs}, {verified_text}, etc.
        failure_template (str, optional): Custom failure template override with variables like {symbol}, {rhs}, {not_verified_text}, etc.
        **kwargs: Optional keyword arguments including:
            language (str): Document-level language override for verification text.
            substitutions (dict): Direct substitution dictionary for custom verification text.

    Returns:
        Markdown: A Markdown object containing the formatted string indicating the verification result.
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
        template_name, success_template_param, failure_template_param
    )

    # Get localized verification text
    verified_text = translate(
        "VERIFIED", language=language, substitutions=substitutions
    )
    not_verified_text = translate(
        "NOT_VERIFIED", language=language, substitutions=substitutions
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

    return Markdown(formatted_result)


def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | dict[str, Any] | None = None,
    sep: str | list[str] | None = None,
    label: str | dict[str, str] | None = None,
    label_command: str | None = None,
    col_wrap: str | dict | list[dict] | Dataframe | tuple | None = None,
    float_format: str | dict | list[dict] | Dataframe | tuple | None = None,
    cell_formatter: 'Callable | dict | list[dict] | Dataframe | tuple | None' = None,
    row_formatter: 'Callable | dict | None' = None,
    debug: bool | None = None,
    env_arg: str | None = None,
    **kwargs: Any,
) -> Markdown:
    """
    Generates a LaTeX equation or equation array based on the provided equations.

    Args:
        eqns (dict | list[dict] | Dataframe): The equations to be displayed. It can be a dictionary, a list of dictionaries, or a Dataframe object.
        environment (str | dict | EnvironmentDefinition, optional): The LaTeX environment to use for displaying the equations.
            Can be a string name (e.g., "align"), a dict defining the environment, or an EnvironmentDefinition object.
            Defaults to config.latex.default_environment.
        sep (str | list[str], optional): The separator to use between the key and value in each equation. It can be a string or a list of strings. Defaults to "&" or "" for specific environments (e.g. equation, gather).
        label (str | dict, optional): The label to attach to the equation. It can be a string or a dictionary. Defaults to None.
        label_command (str, optional): The LaTeX command to use for attaching the label. Defaults to config.latex.default_label_command.
        col_wrap (list[None | tuple], optional): The column wrapping specification for the Dataframe. Defaults to [None, ('=', '')].
        float_format (str, optional): The float format specification for the Dataframe. Defaults to None.
        cell_formatter (Callable | dict | list[dict] | Dataframe | tuple | None, optional): Cell value formatter function(s).
            Can be a single Callable[(value, col_index) -> str], dict mapping columns to formatters,
            list of formatters per column, Dataframe of formatters, or tuple (formatters, default).
            Defaults to config.display.cell_formatter or default_cell_formatter.
        row_formatter (Callable | dict | None, optional): Row-level formatter function(s).
            Can be a single Callable[(row_latex_str) -> str] or dict mapping symbol keys to formatters.
            Defaults to config.display.row_formatter.
        debug (bool, optional): Whether to enable debug mode. Defaults to config.display.debug.
        env_arg (str, optional): Optional argument string for environment (e.g., "{2}" for alignat{2}).
            User provides complete argument including braces. Defaults to None.
        **kwargs: Additional keyword arguments including:
            language (str): Document-level language override for translations. If not provided, uses global language settings.
            substitutions (dict): Direct substitution dictionary for custom translations (highest priority).

    Returns:
        Markdown: The LaTeX equation or equation array displayed as a Markdown object.

    Notes:
        - If `debug` is True, the generated LaTeX code will be printed.
        - If `environment` is not provided, the default environment specified in `config.latex.default_environment` will be used.
        - If `col_wrap` is not provided, the default column wrapping specification will be used.
        - If `float_format` is not provided, the default float format specification will be used.
        - If `label` is not provided, a label will not be attached to the equation.
        - If `label_command` is not provided, the default label command specified in `config.latex.default_label_command` will be used.
        - The `eqns` argument can be a dictionary, a list of dictionaries, or a Dataframe object.
        - The `sep` argument can be a string or a list of strings.
        - The `label` argument can be a string or a dictionary.
        - The `label_command` argument can be a string.
        - The `col_wrap` argument can be a list of None or tuples.
        - The `float_format` argument can be a string.
        - The `debug` argument can be a boolean.
    """

    # set default values
    if not debug:
        debug = config.display.debug

    # Use config default_float_format if not explicitly provided
    if float_format is None:
        float_format = config.display.default_float_format

    # Prepare latex kwargs for formatters (validate and set defaults)
    from keecas.formatters import validate_latex_kwargs

    # Filter out localization parameters that shouldn't go to latex()
    latex_kwargs = {
        k: v for k, v in kwargs.items() if k not in ["language", "substitutions"]
    }

    # Set default mul_symbol if not provided
    if "mul_symbol" not in latex_kwargs:
        latex_kwargs["mul_symbol"] = config.latex.default_mul_symbol

    # Validate latex kwargs
    latex_kwargs = validate_latex_kwargs(latex_kwargs)

    # Handle inline environment definitions
    from keecas.config import EnvironmentDefinition

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

    if not col_wrap:
        col_wrap = config.col_wrap

    # warning message in case of too many labels provided
    if not env_config.supports_multiple_labels and isinstance(label, dict):
        warn(
            f"ATTENTION! label is a dict, while the {environment} does not support multiple labels"
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
    # Convert to Dataframe (same logic as eqns)
    if isinstance(float_format, list):
        float_format = Dataframe(float_format)

    # if float_format is a tuple, then the second value of the tuple is assumed to be the default_value
    float_format = create_dataframe(
        seed=float_format[0] if isinstance(float_format, tuple) else float_format,
        default_value=float_format[1] if isinstance(float_format, tuple) else None,
        keys=keys,
        width=num_cols,
    )

    ### col_wrap
    # if col_wrap is a tuple, then the second value of the tuple is assumed to be the default_value
    col_wrap = create_dataframe(
        seed=col_wrap[0] if isinstance(col_wrap, tuple) else col_wrap,
        default_value=col_wrap[1] if isinstance(col_wrap, tuple) else None,
        keys=keys,
        width=num_cols,
    )

    ### cell_formatter
    # Import default formatter
    from keecas.formatters import default_cell_formatter

    # Step 1: Determine default if not provided
    if cell_formatter is None:
        cell_formatter = config.display.cell_formatter or default_cell_formatter

    # Step 2: Create Dataframe (single line, matching float_format pattern)
    cell_formatters = create_dataframe(
        seed=cell_formatter if not isinstance(cell_formatter, tuple) else cell_formatter[0],
        default_value=default_cell_formatter if not isinstance(cell_formatter, tuple) else cell_formatter[1],
        keys=keys,
        width=num_cols,
    )

    # generate label dict if none is passed
    if not label:
        label = {k: None for k in keys}

    # define label command
    if not label_command:
        label_command = config.latex.default_label_command

    # Generate template using environment configuration
    first_key = list(keys)[0] if keys else None
    template = _generate_environment_template(
        environment, env_config, label, first_key, label_command, env_arg
    )

    # generate the rows
    body_lines = {}
    for key, list_values in eqns.items():
        # Generate cells with custom formatters
        cells = []
        for col_idx, (v, s, cw, ff, cf) in enumerate(zip_longest(
            ([key] + list_values),
            sep,
            col_wrap[key],
            float_format[key],
            cell_formatters[key],  # Add to zip_longest
            fillvalue="",
        )):
            # Apply formatter with column index and latex kwargs
            if v is not None:
                formatted_value = cf(v, col_idx, **latex_kwargs)  # Pass latex kwargs to formatter
                # Note: formatted_value is never None - registry ensures fallback
                cell_content = f"{_col_wrap(cw,v)[0]}{formatted_value}{_col_wrap(cw, v)[-1]}"
            else:
                cell_content = " "

            # Apply float formatting
            cell_content = format_decimal_numbers(f"{cell_content} {s}", ff)
            cells.append(cell_content)

        # Join cells to form row
        body_lines[key] = " ".join(cells) + _attach_label(label, key, label_command)

    # Apply row-level formatters
    if row_formatter is not None:
        if callable(row_formatter):
            # Single function for all rows
            body_lines = {k: row_formatter(v) for k, v in body_lines.items()}
        elif isinstance(row_formatter, dict):
            # Key-specific row formatters (dict keys = symbol keys)
            body_lines = {
                k: row_formatter.get(k, lambda x: x)(v)
                for k, v in body_lines.items()
            }
    elif config.display.row_formatter is not None:
        # Use config default if available
        row_func = config.display.row_formatter
        body_lines = {k: row_func(v) for k, v in body_lines.items()}

    # Use line separator from environment config
    join_token = env_config.line_separator

    # generate the body
    body = join_token.join(body_lines.values())

    # clean the body
    body = replace_all(
        body, language=kwargs.get("language"), substitutions=kwargs.get("substitutions")
    )

    template = template.replace("___body___", body)

    if debug:
        print(template)

    return Markdown(template)


import re


def wrap_floats(text: str, wrapper: tuple[str, str] = ("", "")) -> str:
    # Define a regular expression pattern to match decimal numbers
    float_pattern = re.compile(r"-?\d+\.\d+")

    # Define a function to use as replacement
    def wrap_match(match):
        return f"{wrapper[0]}{match.group(0)}{wrapper[1]}"

    # Use re.sub to replace all matches with the wrapped version
    wrapped_text = float_pattern.sub(wrap_match, text)

    return wrapped_text


def format_decimal_numbers(
    text: str | None, format_string: str | None = None
) -> str | None:
    """
    Finds all decimal numbers in a string, applies a specified format,
    and substitutes them back into the string.

    Args:
        text: The string to search for decimal numbers.
        format_string: The format string to apply (e.g., ".3f", "{:.3f}", ":0.3f").
                      Supports shorthand notation - will be normalized to full format.
                      If None, no formatting is applied.

    Returns:
        The formatted string.

    Raises:
        ValueError: If format_string is invalid or cannot format numbers.
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

    def format_match(match):
        value = float(match.group())
        return normalized_format.format(value)

    return re.sub(r"-?\d+\.\d+", format_match, text)


def dict_to_eq(result: dict[Basic, Any]) -> Eq | list[Eq]:
    eq = [Eq(k, v) for k, v in result.items()]
    return eq if len(eq) > 1 else eq[0]


def eq_to_dict(result: Eq | list[Eq] | tuple[Eq, ...]) -> dict[Basic, Any]:
    if hasattr(result, "__iter__"):
        return {x.lhs: x.rhs for x in result}
    else:
        return {result.lhs: result.rhs}


import regex


def _get_base_replacements() -> dict[str, str | callable]:
    """Get non-localizable replacements that are always applied."""
    return {
        r"\\frac": r"\\dfrac",  # first replace all frac with dfrac
        r"\^\{((?:[^{}]|(?:\{(?1)\}))*)}": lambda m: regex.sub(
            "dfrac", "frac", m.group(0)
        ),  # then replace all dfrac inside ^{} with frac (small exponent)
        r"\b1 \\cdot": r"",
        r"\\\\": rf"\\\\[{config.latex.vertical_skip}]",
        r"\\,": r"{\,}",
    }


def _get_localized_replacements(
    language: str | None = None, substitutions: dict[str, str] | None = None
) -> dict[str, str]:
    """Get localized replacements based on current language settings."""
    return {
        r"\bfor\b": translate("for", language=language, substitutions=substitutions),
        r"\botherwise\b": translate(
            "otherwise", language=language, substitutions=substitutions
        ),
        # Domain/Range labels from SymPy LaTeX output (match \text{...} patterns)
        r"\\text\{Domain: \}": f"\\text{{{translate('Domain: ', language=language, substitutions=substitutions)}}}",
        r"\\text\{Domain on \}": f"\\text{{{translate('Domain on ', language=language, substitutions=substitutions)}}}",
        r"\\text\{Range\}": f"\\text{{{translate('Range', language=language, substitutions=substitutions)}}}",
    }


def get_replacement_dict(
    language: str | None = None, substitutions: dict[str, str] | None = None
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


# Legacy replacement dict for backward compatibility
replacement = get_replacement_dict()


# %% replace all the key, value pair
def replace_all(
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
        reps = get_replacement_dict(language=language, substitutions=substitutions)

    for pattern, repl in reps.items():
        body = regex.sub(pattern, repl, body)
    return body


def latex_inline_dict(var: Basic, mapping: dict[Basic, Any], **kwargs: Any) -> str:
    if not "mul_symbol" in kwargs:
        kwargs["mul_symbol"] = r"\,"
    match (mode := kwargs.get("mode")):
        case "plain" | None:
            wrap = ("", "")
        case "inline":
            wrap = ("$", "$")
        case _:
            wrap = (rf"\begin{{{mode}}}", rf"\end{{{mode}}}")

    kwargs["mode"] = "plain"

    _latex = lambda x: replace_all(latex(x, **kwargs))
    return f"{wrap[0]}{_latex(var)} = {_latex(mapping[var])}{wrap[1]}"


def _col_wrap(
    cw: None | str | tuple[str, str] | dict[type, tuple[str, str]], value: Any
) -> tuple[str, str]:
    if not cw:
        return ("", "")

    if isinstance(cw, str):
        return cw, ""

    if isinstance(cw, tuple):
        return cw

    if isinstance(cw, dict):
        for type, col_wraps in cw.items():
            if isinstance(value, type):
                return col_wraps

    return ("", "")
