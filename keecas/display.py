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

from typing import Union, List, Dict

from .dataframe import *

# DEFINITION OF DEFAULT VALUES

# add {{< include _KaTeX_compatibility.qmd >}} to main qmd file
KaTeX_compatibility = {
    "default_environment": "align",
    "default_label_command": r"\\%\label",
    "default_mul_symbol": r"\,",
}

# default values for labels
from dataclasses import dataclass


@dataclass
class options:
    EQ_PREFIX: str = "eq-"
    EQ_SUFFIX: str = ""
    VERTICAL_SKIP: str = "8pt"
    PRINT_LABEL: bool = False
    DEBUG = False


from itertools import chain, zip_longest


# determina esito verifica
def verifica(lhs, rhs, test=Le) -> Markdown:
    """Determines if the left-hand side (lhs) is less than or equal to
    the right-hand side (rhs) based on the provided test function.

    Args:
        lhs (sympy.Expr): The left-hand side expression.
        rhs (sympy.Expr): The right-hand side expression.
        test (sympy.GreaterThan, sympy.LessThan, sympy.GreaterThanEqual, sympy.LessThanEqual, optional):
            The test function to apply. Defaults to Le (less than or equal to).

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

    if test(lhs, rhs):
        return Markdown(
            rf"\textcolor{{green}}{{\left[{symbol_if_true}{rhs}\quad \textbf{{VERIFICATO}}\right]}}"
        )
    else:
        return Markdown(
            rf"\textcolor{{red}}{{\left[{symbol_if_false}{rhs}\quad \textbf{{NON VERIFICATO}}\right]}}"
        )


def show_eqn(
    eqns: dict | list[dict] | Dataframe,
    environment: str = "align",
    sep: str | list[str] = "&",
    label: str | dict = None,
    label_command: str = None,
    col_wrap: list[None | tuple] = None,
    float_format: str = None,
    debug: bool = None,
    **kwargs,
) -> Markdown:
    """Formats and displays mathematical equations with LaTeX rendering.

    Args:
        eqns (dict | list[dict]): A dictionary or list of dictionaries representing equations.
            Each dictionary key is a variable name, and the value is the corresponding expression.
        environment (str, optional): The LaTeX environment for rendering the equations.
            Defaults to "align" (for aligned equations). Other options include "equation", "align*", etc.
        sep (str | list[str], optional): The separator symbol(s) used between different parts of the equation.
            Defaults to "&" for aligned equations. Can be a string or a list of strings (one per element).
        label (str | dict, optional): A label to add to the equation. Single label as a string or a dictionary
            for multiple labels (not supported for all environments). Defaults to None.
        label_command (str, optional): The LaTeX command for labeling. Defaults to the value from `KaTeX_compatibility` dictionary.
        col_wrap (list[None | tuple], optional): Controls wrapping of elements in each column. Each tuple defines
            wrapping before and after the element (e.g., [None, ('=', '')] for no wrapping in the first column
            and wrapping around the "=" sign in the second). Defaults to `[None, ('=', '')]`.
        float_format (str, optional): The format string for displaying decimal numbers (e.g., ".2f" for two decimal places).
        debug (bool, optional): Enables printing the formatted equation template for debugging purposes. Defaults to False.
        **kwargs: Additional keyword arguments passed to underlying functions (e.g., `myprint_latex`).

    Returns:
        Markdown: A Markdown object containing the formatted equation(s).
    """

    # set defualt values
    if not debug:
        debug = options.DEBUG

    if not "mul_symbol" in kwargs:
        kwargs["mul_symbol"] = KaTeX_compatibility["default_mul_symbol"]

    if not environment:
        environment = KaTeX_compatibility["default_environment"]

    if not col_wrap:
        col_wrap = [
            None,
            ("=", ""),
        ]  # no wrapping for the key element (first columns), then '=' sign for the second column

    if not label_command:
        label_command = KaTeX_compatibility["default_label_command"]

    # add label at the end (does it make sense for * object?)
    if label and not isinstance(label, dict):
        label_at_the_start = rf"{options.EQ_PREFIX}{label}{options.EQ_SUFFIX}"
    else:
        label_at_the_start = ""

    if label_at_the_start and "%" not in label_command:
        full_label_at_the_start = rf"{label_command}{{{label_at_the_start}}}"
    else:
        full_label_at_the_start = ""

    # check if environment is a special (starred "cases*" and "split*" are not valid latex environment, but they need to pass the "*" operator to the "equation" outer environment)
    if environment.replace("*", "") in ["cases", "split"]:

        # determine if outer env is starred
        env = "align*" if "*" in environment else "align"

        # clear the cases|split environment from the star
        environment = "aligned"

        # wrap inner cases|split in outer "align"
        wrap = (
            f"\\begin{{{env}}}{full_label_at_the_start}\n",
            f"\t\\left\\{{\\begin{{{environment}}}",
            f"\t\n\\end{{{environment}}}\\right.",
            f"\n\\end{{{env}}}",
        )

    else:
        # do nothing
        wrap = (
            "",
            f"\\begin{{{environment}}}{full_label_at_the_start}",
            f"\n\\end{{{environment}}}",
            "",
        )

    # warning message in case of too many labels provided
    if environment.replace("*", "") in ["equation", "cases", "split"] and isinstance(
        label, dict
    ):
        warn(
            f"ATTENTION! label is a dict, while the {environment} does not support multiple labels"
        )

    # handle edge case for 'equation' environment
    if "equation" in environment:
        sep = ""  # no separator in environment

    # definition of the main template
    template = f"{wrap[0]}{wrap[1]}\n___body___{wrap[2]}{wrap[3]}"

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
    matrix = {k: [k] + [vv for vv in v] for k, v in eqns.items()}
    # print(f'{matrix=}')

    # create float_format (dict)
    float_format = create_dataframe(seed=float_format, keys=keys, width=num_cols)
    # print(f'{float_format=}')

    ### col_wrap
    # adjust size of the col_wrap; assume None as default (for compatibility with earlier versions)
    col_wrap = create_dataframe(seed=col_wrap, keys=keys, width=num_cols)

    for k, v in col_wrap.items():
        # clean the none value in wrapper with tuple
        col_wrap[k] = [cw if cw is not None else ("", "") for cw in v]
        # substitute single value with tuple, assuming last item is ''
        col_wrap[k] = [cw if isinstance(cw, tuple) else (cw, "") for cw in col_wrap[k]]

    # print(f'{col_wrap=}')

    # generate the rows
    body_lines = {}
    for key, list_values in matrix.items():
        body_lines[key] = " ".join(
            [
                format_decimal_numbers(
                    f'{ f"{cw[0]}{myprint_latex(v, **kwargs)}{cw[-1]}" if v is not None else " " } {s}',
                    ff,
                )
                for v, s, cw, ff in zip_longest(
                    list_values, sep, col_wrap[key], float_format[key], fillvalue=""
                )
            ]
        )

    # how to join the lines of the body
    join_token = "" if "equation" in environment else " \\\\\n "

    # generate the body
    body = join_token.join(body_lines.values())

    # clean the body
    body = replace_all(body, replacement)
    # for pattern, repl in replacement.items():
    #     body = body.replace(pattern, repl)

    # format the decimal numbers
    # if float_format:
    #     body = format_decimal_numbers(body, float_format)

    template = template.replace("___body___", body)

    if debug:
        print(template)

    if options.PRINT_LABEL:
        print(f"{label_at_the_start = :s}") if label_at_the_start else None

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
        return {x.expr.lhs: x.value for x in result}
    else:
        return {result.expr.lhs: result.value}


import regex

# replacements for the regex function
replacement = {
    r"\\frac": r"\\dfrac",  # fisrt replace all frac with dfrac
    r"\^\{((?:[^{}]|(?:\{(?1)\}))*)}": lambda m: regex.sub(
        "dfrac", "frac", m.group(0)
    ),  # then replace all dfrac inside ^{} with frac (small exponent)
    r"\b1 \\cdot": r"",
    r"\\\\": rf"\\\\[{options.VERTICAL_SKIP}]",
    r"for": "per",
    r"otherwise": "altrimenti",
    r"\\,": r"{\,}",
}


# %% replace all the key, value pair
def replace_all(body, reps=replacement):
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
