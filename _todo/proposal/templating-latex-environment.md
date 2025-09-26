# Templating the LaTeX Environment

## Original Objective (from show_eqn refactor)

At the moment the function supports different environments. The logic of this should be converted to a templating system, and the user should be able to provide their own template.

## Analysis of Current Environment Handling

### Current Implementation Issues

Looking at the current `show_eqn` function, environment handling is scattered and hardcoded:

```python
# Hardcoded environment-specific logic
environments_no_sep = ["equation", "gather", "multline"]
if environment in environments_no_sep:
    sep = "" if isinstance(sep, str) else [""]

# Hardcoded LaTeX generation
latex_str += rf"\begin{{{environment}}}"
# ... equation content ...
latex_str += rf"\end{{{environment}}}"
```

### Problems with Current Approach

1. **Hardcoded environment rules**: Special cases are buried in conditional logic
2. **No extensibility**: Users cannot add custom environments or modify existing ones
3. **Inflexible formatting**: LaTeX structure is generated procedurally
4. **Limited customization**: No way to customize environment-specific formatting

## Proposed Templating System

### Core Concept: Environment Templates

Replace hardcoded environment logic with a flexible templating system where each LaTeX environment is defined by a template that specifies:

1. **Structure**: How equations are wrapped and formatted
2. **Separators**: What separators to use (if any)
3. **Labels**: How labels should be handled
4. **Special formatting**: Environment-specific formatting rules

### Template Architecture

#### 1. Template Definition Structure

```python
@dataclass
class EnvironmentTemplate:
    """Template for LaTeX environment generation."""
    name: str
    begin_template: str
    end_template: str
    equation_separator: str | None
    line_separator: str
    supports_labels: bool
    label_placement: Literal["end", "each_line", "none"]
    multi_line: bool

    # Optional formatting hooks
    format_equation: Callable[[str], str] | None = None
    format_content: Callable[[str], str] | None = None
```

#### 2. Built-in Templates

```python
# Built-in environment templates
BUILTIN_TEMPLATES = {
    "align": EnvironmentTemplate(
        name="align",
        begin_template="\\begin{align}",
        end_template="\\end{align}",
        equation_separator="&",
        line_separator=" \\\\\n",
        supports_labels=True,
        label_placement="end",
        multi_line=True
    ),

    "equation": EnvironmentTemplate(
        name="equation",
        begin_template="\\begin{equation}",
        end_template="\\end{equation}",
        equation_separator=None,  # No separator for single equations
        line_separator="",
        supports_labels=True,
        label_placement="end",
        multi_line=False
    ),

    "gather": EnvironmentTemplate(
        name="gather",
        begin_template="\\begin{gather}",
        end_template="\\end{gather}",
        equation_separator=None,
        line_separator=" \\\\\n",
        supports_labels=True,
        label_placement="each_line",
        multi_line=True
    ),

    "cases": EnvironmentTemplate(
        name="cases",
        begin_template="\\begin{cases}",
        end_template="\\end{cases}",
        equation_separator="&",
        line_separator=" \\\\\n",
        supports_labels=False,
        label_placement="none",
        multi_line=True
    )
}
```

#### 3. Advanced Templates with Jinja2

For maximum flexibility, use Jinja2 templating for complex environments:

```python
@dataclass
class AdvancedEnvironmentTemplate:
    """Advanced template using Jinja2 for complex formatting."""
    name: str
    template: str  # Jinja2 template string
    default_context: dict[str, Any]

    def render(self, equations: list[str], labels: list[str] | None = None, **kwargs) -> str:
        """Render template with equations and context."""
```

Example advanced template:
```jinja2
\begin{{{ environment_name }}}
{% if vertical_spacing %}{{ vertical_spacing }}{% endif %}
{% for eq in equations %}
    {{ eq }}{% if labels and labels[loop.index0] %} \label{ {{ labels[loop.index0] }} }{% endif %}
    {% if not loop.last %}{{ line_separator }}{% endif %}
{% endfor %}
\end{{{ environment_name }}}
```

### Template Management System

#### 1. Template Registry

```python
class EnvironmentTemplateRegistry:
    """Registry for managing LaTeX environment templates."""

    def __init__(self):
        self._templates: dict[str, EnvironmentTemplate] = {}
        self._load_builtin_templates()

    def register_template(self, template: EnvironmentTemplate) -> None:
        """Register a new template or override existing one."""

    def get_template(self, name: str) -> EnvironmentTemplate:
        """Get template by name with fallback to 'align'."""

    def list_templates(self) -> list[str]:
        """List all available template names."""

    def load_from_config(self, config_path: Path) -> None:
        """Load user-defined templates from config file."""
```

#### 2. Configuration Integration

```toml
# .keecas/config.toml
[templates.environments]

# Override built-in template
[templates.environments.align]
equation_separator = "&"
line_separator = " \\\\\n"
supports_labels = true

# Define custom template
[templates.environments.custom_align]
begin_template = "\\begin{alignat}{2}"
end_template = "\\end{alignat}"
equation_separator = "&"
line_separator = " \\\\\n"
supports_labels = true
label_placement = "end"

# Advanced template with Jinja2
[templates.environments.fancy_box]
type = "jinja2"
template = """
\\boxed{
\\begin{align}
{% for eq in equations %}
{{ eq }}{% if not loop.last %} \\\\{% endif %}
{% endfor %}
\\end{align}
}
"""
```

### Implementation Plan

#### Phase 1: Core Template System
1. **Design template datastructures**
   - Implement `EnvironmentTemplate` dataclass
   - Create template registry with built-in templates
   - Add template validation logic

2. **Integrate with show_eqn**
   - Replace hardcoded environment logic with template lookups
   - Implement template-based LaTeX generation
   - Maintain backward compatibility

#### Phase 2: Configuration System
3. **Config file integration**
   - Add template configuration parsing
   - Support template overrides and custom definitions
   - Implement template validation and error handling

4. **User template loading**
   - Allow loading templates from config files
   - Support both simple and advanced template formats
   - Add template conflict resolution

#### Phase 3: Advanced Features
5. **Jinja2 integration**
   - Add optional Jinja2 dependency for advanced templates
   - Implement advanced template rendering
   - Create template context management

6. **Template utilities**
   - Add template validation tools
   - Implement template documentation generation
   - Create template debugging utilities

#### Phase 4: Documentation and Examples
7. **Comprehensive documentation**
   - Document template system architecture
   - Provide template creation tutorials
   - Add examples for common use cases

8. **Template library**
   - Create library of useful custom templates
   - Add templates for common engineering environments
   - Provide template sharing guidelines

### Benefits

#### 1. **Extensibility**
- Users can define custom LaTeX environments
- Easy to add support for new packages (e.g., `mathtools`, `amsmath` extensions)
- Template sharing between projects and users

#### 2. **Maintainability**
- Clear separation between environment logic and equation processing
- Declarative template definitions instead of procedural code
- Easier to test and debug environment-specific issues

#### 3. **Flexibility**
- Per-project template customization
- Environment-specific formatting rules
- Support for complex LaTeX structures

#### 4. **User Experience**
- Consistent interface across different environments
- Easy to experiment with different formatting styles
- Reduced need to understand LaTeX internals

### Example Usage

#### Before (current)
```python
# Limited to built-in environments
show_eqn(equations, environment="align")
show_eqn(equations, environment="gather")
# No way to customize environment behavior
```

#### After (with templating)
```python
# Use built-in templates
show_eqn(equations, environment="align")

# Use custom template from config
show_eqn(equations, environment="custom_align")

# Override template inline
custom_template = EnvironmentTemplate(
    name="boxed_align",
    begin_template="\\boxed{\\begin{align}",
    end_template="\\end{align}}",
    equation_separator="&",
    line_separator=" \\\\\n",
    supports_labels=True,
    label_placement="end",
    multi_line=True
)
show_eqn(equations, template=custom_template)
```

### Backward Compatibility

**Guarantee**: All existing environment names will continue to work
- Built-in templates for all currently supported environments
- Same default behavior for existing code
- No changes to function signature (add optional `template` parameter)

### Advanced Template Examples

#### Engineering Calculations
```toml
[templates.environments.calculation]
type = "jinja2"
template = """
\\begin{array}{rcl}
{% for eq in equations %}
{{ eq.lhs }} &=& {{ eq.rhs }}{% if labels and labels[loop.index0] %} \\quad \\text{({{ labels[loop.index0] }})}{% endif %}
{% if not loop.last %} \\\\[0.5em]{% endif %}
{% endfor %}
\\end{array}
"""
```

#### Boxed Equations
```toml
[templates.environments.important]
type = "jinja2"
template = """
\\fboxsep=10pt
\\boxed{
\\begin{aligned}
{% for eq in equations %}
{{ eq }}{% if not loop.last %} \\\\{% endif %}
{% endfor %}
\\end{aligned}
}
"""
```

### Timeline Estimate

- **Phase 1**: 2 days (core system)
- **Phase 2**: 1 day (configuration)
- **Phase 3**: 2 days (advanced features)
- **Phase 4**: 1 day (documentation)

**Total**: ~6 days of development work

### Questions for User Review

1. **Template complexity**: Should we start with simple templates or implement Jinja2 from the beginning?
2. **Built-in templates**: Any specific LaTeX environments that should be included by default?
3. **Configuration format**: TOML vs. separate template files for complex templates?
4. **Dependencies**: Is adding Jinja2 as an optional dependency acceptable?

Awaiting user approval to proceed with implementation.