# %%
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

from typing import Union, List, Dict

from .dataframe import *

# default values for labels
from dataclasses import dataclass

from .config import *
from .localization import translate

class options:
    """Configuration options for keecas display functions."""

    def __init__(self):
        self.EQ_PREFIX: str = "eq-"
        self.EQ_SUFFIX: str = ""
        self.VERTICAL_SKIP: str = "8pt"
        self.PRINT_LABEL: bool = False
        self.DEBUG = False
        self.katex = False
        self.default_mul_symbol = r"\,"
        self.default_environment = "align"
        self.default_label_command = r"\label"
        self._language: str = None  # Private storage for language
        self.col_wrap = [
            None,
            {
                Basic|Quantity|int|float: ("=", ""),
                Markdown|str: (r"\qquad", ""),
                object: ("", ""),
            },
        ]

    @property
    def language(self) -> str:
        """Document-level language override (None = use global/config)."""
        return self._language

    @language.setter
    def language(self, value: str):
        """Set language and automatically update Pint locale and localization manager."""
        self._language = value
        # Update global localization manager when document language changes
        if value is not None:
            from .localization import set_language
            set_language(value)
        # Update Pint locale when language changes
        try:
            from .pint_sympy import update_pint_locale
            update_pint_locale(value)
        except ImportError:
            # Handle case where pint_sympy module is not available
            pass


# Create global options instance
options = options()



from itertools import chain, zip_longest


# check verification result
def check(lhs, rhs, test=Le, **kwargs) -> Markdown:
    """Determines if the left-hand side (lhs) is less than or equal to
    the right-hand side (rhs) based on the provided test function.

    Args:
        lhs (sympy.Expr): The left-hand side expression.
        rhs (sympy.Expr): The right-hand side expression.
        test (sympy.GreaterThan, sympy.LessThan, sympy.GreaterThanEqual, sympy.LessThanEqual, optional):
            The test function to apply. Defaults to Le (less than or equal to).
        **kwargs: Optional keyword arguments including:
            language (str): Document-level language override for verification text.
                If not provided, uses global language settings.
            substitutions (dict): Direct substitution dictionary for custom verification text
                (highest priority).

    Returns:
        Markdown: A Markdown object containing the formatted string indicating the verification result (green for success, red for failure).
    """
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

    # Extract localization parameters from kwargs
    language = kwargs.get('language')
    substitutions = kwargs.get('substitutions')

    # Get localized verification text
    verified_text = translate("VERIFIED", language=language, substitutions=substitutions)
    not_verified_text = translate("NOT_VERIFIED", language=language, substitutions=substitutions)

    if test(lhs, rhs):
        return Markdown(
            rf"\textcolor{{green}}{{\left[{symbol_if_true}{rhs}\quad \textbf{{{verified_text}}}\right]}}"
        )
    else:
        return Markdown(
            rf"\textcolor{{red}}{{\left[{symbol_if_false}{rhs}\quad \textbf{{{not_verified_text}}}\right]}}"
        )


# Backward compatibility alias
verifica = check


def show_eqn(
    eqns: dict | list[dict] | Dataframe,
    environment: str = None,
    sep: str | list[str] = "&",
    label: str | dict = None,
    label_command: str = None,
    col_wrap: list[None | tuple] = None,
    float_format: str = None,
    debug: bool = None,
    **kwargs,
) -> Markdown:
    """
    Generates a LaTeX equation or equation array based on the provided equations.

    Args:
        eqns (dict | list[dict] | Dataframe): The equations to be displayed. It can be a dictionary, a list of dictionaries, or a Dataframe object.
        environment (str, optional): The LaTeX environment to use for displaying the equations. Defaults to options.default_environment.
        sep (str | list[str], optional): The separator to use between the key and value in each equation. It can be a string or a list of strings. Defaults to "&" or "" for specific environments (e.g. equation, gather).
        label (str | dict, optional): The label to attach to the equation. It can be a string or a dictionary. Defaults to None.
        label_command (str, optional): The LaTeX command to use for attaching the label. Defaults to options.default_label_command.
        col_wrap (list[None | tuple], optional): The column wrapping specification for the Dataframe. Defaults to [None, ('=', '')].
        float_format (str, optional): The float format specification for the Dataframe. Defaults to None.
        debug (bool, optional): Whether to enable debug mode. Defaults to options.DEBUG.
        **kwargs: Additional keyword arguments including:
            language (str): Document-level language override for translations. If not provided, uses global language settings.
            substitutions (dict): Direct substitution dictionary for custom translations (highest priority).
            Other kwargs are passed to the `myprint_latex` function.

    Returns:
        Markdown: The LaTeX equation or equation array displayed as a Markdown object.

    Notes:
        - If `debug` is True, the generated LaTeX code will be printed.
        - If `environment` is not provided, the default environment specified in `options.default_environment` will be used.
        - If `col_wrap` is not provided, the default column wrapping specification will be used.
        - If `float_format` is not provided, the default float format specification will be used.
        - If `label` is not provided, a label will not be attached to the equation.
        - If `label_command` is not provided, the default label command specified in `options.default_label_command` will be used.
        - The `eqns` argument can be a dictionary, a list of dictionaries, or a Dataframe object.
        - The `sep` argument can be a string or a list of strings.
        - The `label` argument can be a string or a dictionary.
        - The `label_command` argument can be a string.
        - The `col_wrap` argument can be a list of None or tuples.
        - The `float_format` argument can be a string.
        - The `debug` argument can be a boolean.
        - The `**kwargs` argument can be any additional keyword arguments to be passed to the `myprint_latex` function.
    """

    # set default values
    if not debug:
        debug = options.DEBUG

    if not "mul_symbol" in kwargs:
        kwargs["mul_symbol"] = options.default_mul_symbol

    # Filter out localization parameters that shouldn't go to myprint_latex
    latex_kwargs = {k: v for k, v in kwargs.items() if k not in ['language', 'substitutions']}

    if not environment:
        environment = options.default_environment

    if not col_wrap:
        col_wrap = options.col_wrap

    # warning message in case of too many labels provided
    single_label_env = ["equation", "cases", "split"]
    if environment.replace("*", "") in single_label_env and isinstance(label, dict):
        warn(
            f"ATTENTION! label is a dict, while the {environment} does not support multiple labels"
        )

    # handle edge case for 'equation' and 'gather' environment
    if environment.replace("*", "") in ["equation", "gather"]:
        sep = ""  # no separator in environment

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

    # generate the matrix (list[list]]) of keys, many values (first element is the key)
    # matrix = {k: [k] + [vv for vv in v] for k, v in eqns.items()}
    # print(f'{matrix=}')

    # create float_format (dict)
    if isinstance(float_format, tuple):
        float_format = create_dataframe(
            seed=float_format[0],
            default_value=float_format[1],
            keys=keys,
            width=num_cols,
        )
    else:
        float_format = create_dataframe(seed=float_format, keys=keys, width=num_cols)
    # print(f'{float_format=}')

    ### col_wrap
    # adjust size of the col_wrap; assume None as default (for compatibility with earlier versions)
    col_wrap = create_dataframe(seed=col_wrap, keys=keys, width=num_cols, default_value=col_wrap[-1])

    # generate label dict if none is passed
    if not label:
        label = {k: None for k in keys}

    # define label command
    if not label_command:
        label_command = options.default_label_command

    def attach_label(key):
        """
        Attaches a label to a given key.

        Parameters:
            key (str): The key to attach the label to.

        Returns:
            str: The label attached to the key. If the label is empty or the katex engine is being used for rendering (i.e. in a Jupyter notebook), an empty string is returned.

        Notes:
            - The label is constructed using the `options.EQ_PREFIX`, the value of `label[key]`, and `options.EQ_SUFFIX`.
            - If `options.PRINT_LABEL` is True, the key and label are printed.
            - The label is wrapped in a LaTeX command specified by `label_command` if it is not empty and the katex engine is not being used for rendering.
        """

        if isinstance(label, dict):
            text_label = (
                rf"{options.EQ_PREFIX}{label[key]}{options.EQ_SUFFIX}"
                if label.get(key)
                else ""
            )
            if options.PRINT_LABEL:
                print(f"{key}: {text_label}") if text_label else None

            return (
                rf" {label_command}{{{text_label}}} "
                if label.get(key)
                and not options.katex  # don't add the label if there is no label to add, and if katex engine is used for rendering (i.e. jupyter notebook)
                else ""
            )

        if isinstance(label, str) and not key:

            text_label = rf"{options.EQ_PREFIX}{label}{options.EQ_SUFFIX}"

            if options.PRINT_LABEL:
                print(f"label: {text_label}" if text_label else None)

            return (
                rf" {label_command}{{{text_label}}} "
                if not options.katex  # don't add the label if there is no label to add, and if katex engine is used for rendering (i.e. jupyter notebook)
                else ""
            )

        return ""

    # check if environment is special (starred "cases*" and "split*" are not valid latex environment, but they need to pass the "*" operator to the "equation" outer environment)
    if environment.replace("*", "") in ["cases", "split"]:

        # determine if outer env is starred
        env = "align*" if "*" in environment else "align"

        # clear the cases|split environment from the star
        environment = "aligned"

        # wrap inner cases|split in outer "align"
        wrap = (
            f"\\begin{{{env}}}{attach_label(None)}\n",  # for an equation environment, only one label is allowed
            f"\t\\left\\{{\\begin{{{environment}}}",
            f"\t\n\\end{{{environment}}}\\right.",
            f"\n\\end{{{env}}}",
        )

    else:
        # do nothing
        wrap = (
            "",
            f"\\begin{{{environment}}}{attach_label(list(keys)[0]) if environment.replace('*', '') in single_label_env else ''}",
            f"\n\\end{{{environment}}}",
            "",
        )

    # definition of the main template
    template = f"{wrap[0]}{wrap[1]}\n___body___{wrap[2]}{wrap[3]}"

    # generate the rows
    body_lines = {}
    for key, list_values in eqns.items():
        body_lines[key] = " ".join(
            [
                format_decimal_numbers(
                    f'{ f"{_col_wrap(cw,v)[0]}{myprint_latex(v, **latex_kwargs)}{_col_wrap(cw, v)[-1]}" if v is not None else " " } {s}',
                    ff,
                )
                for v, s, cw, ff in zip_longest(
                    ([key] + list_values),
                    sep,
                    col_wrap[key],
                    float_format[key],
                    fillvalue="",
                )
            ]
        ) + attach_label(key)

    # how to join the lines of the body
    join_token = "" if "equation" in environment else " \\\\\n "

    # generate the body
    body = join_token.join(body_lines.values())

    # clean the body
    body = replace_all(body, language=kwargs.get('language'), substitutions=kwargs.get('substitutions'))

    template = template.replace("___body___", body)

    if debug:
        print(template)

    return Markdown(template)


def myprint_latex(expr: Basic | str | Markdown, **kwargs) -> str:
    """Converts a mathematical expression to a LaTeX string.

    This function handles different input types and allows for customization of the output format.

    Args:
        expr (Basic | str | Markdown): The mathematical expression to convert.
            * Basic (SymPy): A SymPy expression object.
            * str: A string representation of a mathematical expression.
            * Markdown: A Markdown object that likely contains LaTeX code (data attribute is extracted).
        **kwargs: Additional keyword arguments passed to the SymPy `latex` function for formatting the output.

    Returns:
        str: The LaTeX string representation of the mathematical expression.
    """
    if isinstance(expr, Markdown):
        return expr.data

    return latex(expr, **kwargs)


import re


def wrap_floats(text, wrapper=("", "")):
    # Define a regular expression pattern to match decimal numbers
    float_pattern = re.compile(r"-?\d+\.\d+")

    # Define a function to use as replacement
    def wrap_match(match):
        return f"{wrapper[0]}{match.group(0)}{wrapper[1]}"

    # Use re.sub to replace all matches with the wrapped version
    wrapped_text = float_pattern.sub(wrap_match, text)

    return wrapped_text


def format_decimal_numbers(text, format_string="{:.2f}"):
    """
    Finds all decimal numbers in a string, applies a specified format,
    and substitutes them back into the string.

    Args:
        text: The string to search for decimal numbers.
        format_string: The format string to apply to the decimal numbers.

    Returns:
        The formatted string.
    """
    if text is None or format_string is None:
        return text

    def format_match(match):
        value = float(match.group())
        return format_string.format(value)

    return re.sub(r"-?\d+\.\d+", format_match, text)


def dict_to_eq(result: dict):
    eq = [Eq(k, v) for k, v in result.items()]
    return eq if len(eq) > 1 else eq[0]


def eq_to_dict(result: Eq | list | tuple):
    if hasattr(result, "__iter__"):
        return {x.lhs: x.rhs for x in result}
    else:
        return {result.lhs: result.rhs}


import regex

def _get_base_replacements():
    """Get non-localizable replacements that are always applied."""
    return {
        r"\\frac": r"\\dfrac",  # first replace all frac with dfrac
        r"\^\{((?:[^{}]|(?:\{(?1)\}))*)}": lambda m: regex.sub(
            "dfrac", "frac", m.group(0)
        ),  # then replace all dfrac inside ^{} with frac (small exponent)
        r"\b1 \\cdot": r"",
        r"\\\\": rf"\\\\[{options.VERTICAL_SKIP}]",
        r"\\,": r"{\,}",
    }

def _get_localized_replacements(language: str = None, substitutions: dict = None):
    """Get localized replacements based on current language settings."""
    return {
        r"\bfor\b": translate("for", language=language, substitutions=substitutions),
        r"\botherwise\b": translate("otherwise", language=language, substitutions=substitutions),
    }

def get_replacement_dict(language: str = None, substitutions: dict = None):
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
def replace_all(body, reps=None, language=None, substitutions=None):
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


def latex_inline_dict(var, mapping: dict, **kwargs):
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


def _col_wrap(cw: None | str | tuple[str, str] | dict, value) -> tuple[str, str]:
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