# Task: Post-Publication Marketing Posts

**Status**: Proposal (awaiting user review)
**Created**: 2025-01-13
**Original Objective**: Create marketing posts for Reddit, Quarto forums, and LinkedIn to announce keecas publication

## Objective

Create engaging marketing posts for three platforms (Reddit, Quarto forums, LinkedIn) to announce the publication of keecas. Each post should follow a consistent structure: brief description, code example from docs/index.qmd, and link to documentation. Platform-specific instructions and formatting will be provided by user.

## General Post Structure

All posts will follow this template:
1. **Brief description**: Introduce keecas and its value proposition
2. **Code example**: Use the example from docs/index.qmd (already read at session start)
3. **Documentation link**: https://kompre.github.io/keecas/

## Target Platforms

1. **Reddit**: Platform-specific formatting and subreddit targeting TBD by user
2. **Quarto Forums**: Platform-specific guidelines TBD by user
3. **LinkedIn**: Professional tone and formatting TBD by user

## Implementation Steps

1. **Preparation Phase**
   - Review docs/index.qmd example code (already available in context)
   - Extract and format the quick example from lines 26-64
   - Prepare base description highlighting:
     - Dict-based equation system
     - Unit-aware calculations with Pint
     - Automatic LaTeX rendering for Quarto
     - Multi-language support

2. **Platform-Specific Drafts**
   - Create draft for Reddit (awaiting user guidelines)
   - Create draft for Quarto forums (awaiting user guidelines)
   - Create draft for LinkedIn (awaiting user guidelines)

3. **Review and Iteration**
   - Submit drafts to user for review
   - Incorporate feedback and finalize

## Code Example (from docs/index.qmd)

The example to be included (lines 26-64):

```python
from keecas import symbols, u, pc, show_eqn, generate_unique_label

# Define symbols with LaTeX notation
F_d, A_load, sigma = symbols(r"F_{d}, A_{load}, \sigma")

# Parameters with units
_p = {
    F_d: 10 * u.kN,
    A_load: 50 * u.cm**2,
}

# Expressions
_e = {
    sigma: "F_d / A_load" | pc.parse_expr
}

# Evaluate
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# Description
_d = {
    F_d: "design force",
    A_load: "loaded area",
    sigma: "normal stress",
}

# Label (Quarto only)
_l = generate_unique_label(_d)

# Display
show_eqn(
    [_p | _e, _v, _d], # list of dict as main input
    label=_l # a dict of labels (key matching)
)
```

## Key Talking Points

- **Dict-based equations**: Keys = LHS symbols, Values = RHS expressions
- **Minimal boilerplate**: Use `_p`, `_e`, `_v` conventions for clean notebooks
- **Unit-aware**: Built on Pint for automatic unit conversion
- **Beautiful LaTeX output**: Automatic amsmath rendering for Quarto PDF/HTML
- **Multi-language**: 10 languages supported with localized units
- **Jupyter-first**: Designed for engineering calculations in notebooks

## Awaiting User Input

Please provide platform-specific instructions for:
1. **Reddit**: Target subreddits, formatting preferences, character limits
2. **Quarto Forums**: Post category, discussion format preferences
3. **LinkedIn**: Professional tone guidelines, hashtag strategy, article vs. post format

## Timeline

- Awaiting user guidelines for each platform
- Draft creation: ~1 hour after guidelines received
- Review cycle: TBD by user
- Publication: User will handle posting to each platform

<!-- write a ned md file for each platform in the .release_announcement folder (it will not be tracked in git). Add link back here so you know what to look for -->
