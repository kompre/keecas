# DEFINITION OF DEFAULT VALUES

from dataclasses import dataclass

from sympy import Basic
from IPython.display import Markdown


@dataclass
class defaults:
    EQ_PREFIX: str = "eq-"
    EQ_SUFFIX: str = ""
    VERTICAL_SKIP: str = "8pt"
    PRINT_LABEL: bool = False
    DEBUG = False
    katex = False
    default_mul_symbol = r"\,"
    default_environment = "align"
    default_label_command = r"\label"
    col_wrap = [
        None,
        {
            Basic: ("=", ""),
            Markdown|str: (r"\qquad", ""),
            object: ("", ""),
        },
    ]