# Configuration

Keecas uses a hierarchical TOML configuration system that allows you to customize behavior at both global and project levels.

## Configuration Files

### File Locations

- **Global**: `~/.keecas/config.toml` (user-wide settings)
- **Local**: `<project>/.keecas/config.toml` (project-specific settings)

### Priority Order

Local > Global > Defaults

## CLI Configuration Management

### Initialize Configuration

```bash
# Create global configuration
keecas config init --global

# Create local configuration
keecas config init --local
```

### Edit Configuration

```bash
# Edit with terminal editor ($EDITOR)
keecas config edit --global
keecas config edit --local

# Open with system default editor (GUI)
keecas config open --global
keecas config open --local
```

### View Configuration

```bash
# Show merged configuration (local + global + defaults)
keecas config show

# Show only global configuration
keecas config show --global

# Show only local configuration
keecas config show --local

# Show configuration file paths
keecas config path
```

### Reset Configuration

```bash
# Reset to defaults (with confirmation)
keecas config reset --global
keecas config reset --local

# Force reset without confirmation
keecas config reset --global --force
```

## Configuration Options

### Language and Localization

```toml
# Language for units and verification text
language = "en"  # en, de, es, fr, it, pt

# Disable automatic Pint locale setting
disable_pint_locale = false
```

**Supported Languages:**
- **Full support**: German (de), Spanish (es), French (fr), Italian (it), Portuguese (pt)
- **Partial support**: Danish (da), Dutch (nl), Norwegian (no), Swedish (sv)
- **Default**: English (en)

### Display Settings

```toml
# KaTeX compatibility (disable \label{})
katex = true

# Print labels in development mode
print_label = false

# Debug mode
debug = false

# Default multiplication symbol for LaTeX
default_mul_symbol = "\\,"
```

### LaTeX Equation Settings

```toml
# Equation label prefix
eq_prefix = "eq-"

# Equation label suffix
eq_suffix = ""

# Vertical spacing around equations
vertical_skip = "8pt"

# Default LaTeX environment
default_environment = "align"

# Default label command
default_label_command = "\\label"
```

### Unit Formatting

```toml
# Default format for Pint quantities
pint_default_format = ".3f~P"

# Language mode for Pint
pint_language_mode = "auto"  # "auto" or "manual"
```

### Custom Translations

Override built-in verification text:

```toml
[custom_translations]
"VERIFIED" = "VERIFICATO"
"NOT_VERIFIED" = "NON VERIFICATO"
"DOMAIN" = "DOMINIO"
"RANGE" = "INTERVALLO"
```

## Runtime Configuration

You can also modify configuration at runtime in your notebooks:

```python
from keecas import config

# Modify display settings
config.katex = True
config.eq_prefix = "eq-calc-"
config.language = "it"

# Check current settings
print(f"Current language: {config.language}")
print(f"KaTeX mode: {config.katex}")
```

## Example Configurations

### Engineering Project (English)

```toml
# .keecas/config.toml
language = "en"
katex = true
eq_prefix = "eq-"
pint_default_format = ".3f~P"
default_environment = "align"

[custom_translations]
# No custom translations needed for English
```

### Italian Engineering Project

```toml
# .keecas/config.toml
language = "it"
katex = true
eq_prefix = "eq-"
pint_default_format = ".3f~P"
vertical_skip = "10pt"

[custom_translations]
"VERIFIED" = "VERIFICATO"
"NOT_VERIFIED" = "NON VERIFICATO"
```

### Research Paper (Minimal Labels)

```toml
# .keecas/config.toml
language = "en"
katex = false  # Full LaTeX support
print_label = false
eq_prefix = "eq-paper-"
default_environment = "equation"
```

### Development/Debug Mode

```toml
# .keecas/config.toml
debug = true
print_label = true
katex = true
eq_prefix = "eq-debug-"
```

## Automatic Language Synchronization

When you change the `language` setting, Keecas automatically:

1. Updates Pint locale for unit formatting
2. Updates localization manager for verification text
3. Synchronizes both global and local configurations

```python
# This automatically updates both Keecas and Pint
config.language = 'de'
```

## Configuration Templates

### Create Template Configurations

Save common configurations as templates:

```bash
# Save current config as template
cp .keecas/config.toml ~/.keecas/templates/engineering.toml

# Use template for new project
cp ~/.keecas/templates/engineering.toml .keecas/config.toml
```

### Project-Specific Overrides

Keep global defaults but override specific settings locally:

```toml
# ~/.keecas/config.toml (global)
language = "en"
katex = true
eq_prefix = "eq-"
pint_default_format = ".3f~P"
```

```toml
# .keecas/config.toml (local override)
language = "it"  # Override language for this project
eq_prefix = "eq-bridge-"  # Project-specific prefix
```

## Troubleshooting

### Configuration Not Loading

1. Check file paths: `keecas config path`
2. Validate TOML syntax: Use a TOML validator
3. Check permissions on configuration directories

### Language/Locale Issues

1. Disable Pint locale if problematic: `disable_pint_locale = true`
2. Check available locales on your system
3. Use English as fallback: `language = "en"`

### KaTeX Compatibility

For Quarto/KaTeX compatibility:
```toml
katex = true  # Disables \label{} commands
```

## Next Steps

- Learn about [Conventions](../user-guide/conventions.md) for using configuration effectively
- Explore [Examples](../user-guide/examples.md) with different configuration setups
- Check the [API Reference](../api-reference/config.md) for programmatic configuration access