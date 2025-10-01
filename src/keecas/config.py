"""
Unified Configuration Management for Keecas.

Manages all configuration options with TOML file support, priority handling,
and dynamic propagation to affected subsystems.
"""

import os
import toml
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Any
from sympy import Basic
from IPython.display import Markdown


@dataclass
class LatexConfig:
    """LaTeX equation output configuration."""
    eq_prefix: str = "eq-"
    eq_suffix: str = ""
    vertical_skip: str = "8pt"
    default_environment: str = "align"
    default_label_command: str = r"\label"
    default_mul_symbol: str = r"\,"
    environments: 'EnvironmentConfig' = field(default_factory=lambda: None)

    def __post_init__(self):
        """Initialize environments if not provided."""
        if self.environments is None:
            self.environments = EnvironmentConfig()


@dataclass
class DisplayConfig:
    """Display and debugging behavior configuration."""
    print_label: bool = False
    debug: bool = False
    katex: bool = False
    default_float_format: str | None = None


@dataclass
class LanguageConfig:
    """Language and localization configuration."""
    _language: str | None = field(default=None, init=False)
    disable_pint_locale: bool = False
    pint_language_mode: str = "auto"  # "auto" or "manual"

    @property
    def language(self) -> str | None:
        """Document-level language override (None = use global/config)."""
        return self._language

    @language.setter
    def language(self, value: str | None):
        """Set language and automatically update Pint locale and localization manager."""
        self._language = value
        # Trigger propagation through the config manager
        if hasattr(self, '_config_manager_ref'):
            self._config_manager_ref._propagate_changes('language', value)


@dataclass
class UnitsConfig:
    """Units formatting configuration."""
    pint_default_format: str = ".2f~P"


@dataclass
class TranslationsConfig:
    """Custom term translations configuration."""
    translations: dict[str, str] = field(default_factory=dict)


@dataclass
class CheckTemplateConfig:
    """Check function template configuration."""
    success_template: str = r"$\textcolor{{green}}{{\left[{symbol}{rhs}\quad \textbf{{{verified_text}}}\right]}}$"
    failure_template: str = r"$\textcolor{{red}}{{\left[{symbol}{rhs}\quad \textbf{{{not_verified_text}}}\right]}}$"
    # Named template sets
    template_sets: dict[str, dict[str, str]] = field(default_factory=lambda: {
        "default": {
            "success": r"$\textcolor{{green}}{{\left[{symbol}{rhs}\quad \textbf{{{verified_text}}}\right]}}$",
            "failure": r"$\textcolor{{red}}{{\left[{symbol}{rhs}\quad \textbf{{{not_verified_text}}}\right]}}$"
        },
        "boxed": {
            "success": r"\colorbox{{green}}{{${symbol}{rhs} \; \checkmark \; \textbf{{{verified_text}}}$}}",
            "failure": r"\colorbox{{red}}{{${symbol}{rhs} \; \times \; \textbf{{{not_verified_text}}}$}}"
        },
        "minimal": {
            "success": r"${symbol}{rhs} \,\textcolor{{green}}{{\checkmark}}$",
            "failure": r"${symbol}{rhs} \,\textcolor{{red}}{{\times}}$"
        }
    })


@dataclass
class EnvironmentDefinition:
    """Single LaTeX environment definition."""
    separator: str
    line_separator: str
    supports_multiple_labels: bool
    outer_environment: str
    inner_environment: str | None = None
    inner_prefix: str = ""
    inner_suffix: str = ""
    outer_prefix: str = ""
    outer_suffix: str = ""
    label_position: str = "outer"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'EnvironmentDefinition':
        """Create from dictionary, filtering unknown keys."""
        valid_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        # Convert empty string to None for inner_environment
        if 'inner_environment' in filtered_data and filtered_data['inner_environment'] == '':
            filtered_data['inner_environment'] = None
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EnvironmentConfig:
    """LaTeX environment configurations accessible via dot notation.

    Access environments as attributes: config.environments.align.separator
    """
    def __init__(self):
        # Standard align environment
        self.align = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=True,
            outer_environment="align",
            inner_environment=None
        )

        # Standard equation environment
        self.equation = EnvironmentDefinition(
            separator="",
            line_separator="",
            supports_multiple_labels=False,
            outer_environment="equation",
            inner_environment=None
        )

        # Standard gather environment
        self.gather = EnvironmentDefinition(
            separator="",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=True,
            outer_environment="gather",
            inner_environment=None
        )

        # Special cases environment - nested structure
        self.cases = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=False,
            outer_environment="align",
            inner_environment="aligned",
            inner_prefix=r"\left\{",
            inner_suffix=r"\right.",
            label_position="outer"
        )
        
        # Special right cases environment - nested structure
        self.rcases = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=False,
            outer_environment="align",
            inner_environment="aligned",
            inner_prefix=r"\left.",
            inner_suffix=r"\right\}",
            label_position="outer"
        )


        # Special split environment - nested structure
        self.split = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=False,
            outer_environment="align",
            inner_environment="aligned",
            label_position="outer"
        )

        # alignat environment - requires argument for number of column pairs
        self.alignat = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=True,
            outer_environment="alignat",
            inner_environment=None
        )

    def get(self, name: str) -> EnvironmentDefinition | None:
        """Get environment by name, returns None if not found."""
        return getattr(self, name, None)

    def set(self, name: str, definition: EnvironmentDefinition | dict[str, Any]) -> None:
        """Set environment by name. Accepts EnvironmentDefinition or dict."""
        if isinstance(definition, dict):
            definition = EnvironmentDefinition.from_dict(definition)
        setattr(self, name, definition)

    def keys(self):
        """Return environment names (attributes that are EnvironmentDefinition)."""
        return [k for k, v in self.__dict__.items() if isinstance(v, EnvironmentDefinition)]

    def items(self):
        """Return (name, definition) pairs."""
        return [(k, v) for k, v in self.__dict__.items() if isinstance(v, EnvironmentDefinition)]


@dataclass
class ConfigOptions:
    """
    Unified configuration for Keecas with proper TOML sections.
    """
    latex: LatexConfig = field(default_factory=LatexConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    language_config: LanguageConfig = field(default_factory=LanguageConfig)
    units: UnitsConfig = field(default_factory=UnitsConfig)
    translations: TranslationsConfig = field(default_factory=TranslationsConfig)
    check_templates: CheckTemplateConfig = field(default_factory=CheckTemplateConfig)

    def __post_init__(self):
        """Set up cross-references for language propagation."""
        self.language_config._config_manager_ref = getattr(self, '_config_manager_ref', None)

    @property
    def language_setting(self) -> str | None:
        return self.language_config.language

    @language_setting.setter
    def language_setting(self, value: str | None):
        self.language_config.language = value

    # Backward compatibility - delegate to language_setting
    def get_language(self) -> str | None:
        return self.language_setting

    def set_language(self, value: str | None):
        self.language_setting = value

    # Backward compatibility property for options.language
    # Note: This shadows the language field, but that's intentional for backward compatibility
    @property
    def language(self) -> str | None:
        return self.language_setting

    @language.setter
    def language(self, value: str | None):
        self.language_setting = value

    @property
    def pint_default_format(self) -> str:
        return self.units.pint_default_format

    @pint_default_format.setter
    def pint_default_format(self, value: str):
        self.units.pint_default_format = value

    @property
    def disable_pint_locale(self) -> bool:
        return self.language_config.disable_pint_locale

    @disable_pint_locale.setter
    def disable_pint_locale(self, value: bool):
        self.language_config.disable_pint_locale = value

    @property
    def custom_translations_dict(self) -> dict[str, str]:
        return self.translations.translations

    @custom_translations_dict.setter
    def custom_translations_dict(self, value: dict[str, str]):
        self.translations.translations = value

    # Complex options (not easily serializable to TOML)
    col_wrap: list = field(default_factory=lambda: [
        None,
        {
            Basic: ("=", ""),
            Markdown: (r"\qquad", ""),
            str: (r"\qquad", ""),
            int: ("=", ""),
            float: ("=", ""),
            object: ("", ""),
        },
    ])

    def to_toml_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for TOML serialization."""
        data = {
            'latex': {
                'eq_prefix': self.latex.eq_prefix,
                'eq_suffix': self.latex.eq_suffix,
                'vertical_skip': self.latex.vertical_skip,
                'default_environment': self.latex.default_environment,
                'default_label_command': self.latex.default_label_command,
                'default_mul_symbol': self.latex.default_mul_symbol,
                'environments': {name: env.to_dict() for name, env in self.latex.environments.items()},
            },
            'display': {
                'print_label': self.display.print_label,
                'debug': self.display.debug,
                'katex': self.display.katex,
                'default_float_format': self.display.default_float_format,
            },
            'language': {
                'disable_pint_locale': self.language_config.disable_pint_locale,
                'pint_language_mode': self.language_config.pint_language_mode,
            },
            'units': {
                'pint_default_format': self.units.pint_default_format,
            },
            'check_templates': {
                'success_template': self.check_templates.success_template,
                'failure_template': self.check_templates.failure_template,
                'template_sets': self.check_templates.template_sets,
            },
        }

        # Add language if set
        if self.language_config.language is not None:
            data['language']['language'] = self.language_config.language

        # Add custom translations if any
        if self.translations.translations:
            data['translations'] = self.translations.translations

        return data

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update configuration from dictionary (loaded from TOML)."""
        for section_key, section_data in data.items():
            if section_key == 'latex' and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if key == 'environments' and isinstance(value, dict):
                        # Handle nested environments under latex
                        for env_name, env_config in value.items():
                            if isinstance(env_config, dict):
                                self.latex.environments.set(env_name, env_config)
                    elif hasattr(self.latex, key):
                        setattr(self.latex, key, value)
            elif section_key == 'display' and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if hasattr(self.display, key):
                        setattr(self.display, key, value)
            elif section_key == 'language' and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if key == 'language':
                        # Use the property setter to trigger propagation
                        self.language_config.language = value
                    elif hasattr(self.language_config, key):
                        setattr(self.language_config, key, value)
            elif section_key == 'units' and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if hasattr(self.units, key):
                        setattr(self.units, key, value)
            elif section_key == 'translations' and isinstance(section_data, dict):
                self.translations.translations.update(section_data)
            elif section_key == 'check_templates' and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if hasattr(self.check_templates, key):
                        setattr(self.check_templates, key, value)
            elif hasattr(self, section_key):
                setattr(self, section_key, section_data)


class ConfigManager:
    """
    Manages configuration files, priority loading, and option propagation.

    Priority order: API overrides > Local config > Global config > Defaults
    """

    def __init__(self):
        self._options = ConfigOptions()
        # Set back-reference for language propagation
        self._options._config_manager_ref = self
        self._options.language_config._config_manager_ref = self
        self._global_config_path = self._get_global_config_path()
        self._local_config_path = self._get_local_config_path()
        self._loaded_files = []
        self.load_configs()

    def _get_global_config_path(self) -> Path:
        """Get path to global configuration file."""
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("USERPROFILE", "")) / ".keecas"
        else:  # Linux/Mac
            config_dir = Path.home() / ".keecas"

        return config_dir / "config.toml"

    def _get_local_config_path(self) -> Path:
        """Get path to local configuration file."""
        return Path.cwd() / ".keecas" / "config.toml"

    def load_configs(self) -> None:
        """Load configurations from files in priority order."""
        self._loaded_files = []

        # Load global config first (lower priority)
        if self._global_config_path.exists():
            try:
                with open(self._global_config_path, "r", encoding="utf-8") as f:
                    global_config = toml.load(f)
                self._options.update_from_dict(global_config)
                self._loaded_files.append(str(self._global_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load global config from {self._global_config_path}: {e}")

        # Load local config second (higher priority)
        if self._local_config_path.exists():
            try:
                with open(self._local_config_path, "r", encoding="utf-8") as f:
                    local_config = toml.load(f)
                self._options.update_from_dict(local_config)
                self._loaded_files.append(str(self._local_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load local config from {self._local_config_path}: {e}")

    def save_config(self, global_config: bool = False, force: bool = False) -> bool:
        """
        Save current configuration to file.

        Args:
            global_config: If True, save to global config file
            force: If True, overwrite existing file

        Returns:
            True if saved successfully, False otherwise
        """
        config_path = self._global_config_path if global_config else self._local_config_path

        if config_path.exists() and not force:
            print(f"Config file already exists: {config_path}")
            print("Use --force to overwrite or edit the existing file.")
            return False

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self._options.to_toml_dict()
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
            print(f"Configuration saved to: {config_path}")
            return True
        except OSError as e:
            print(f"Error saving config to {config_path}: {e}")
            return False

    def init_config(self, global_config: bool = False, force: bool = False, comment_style: str = "##") -> bool:
        """Initialize a new configuration file with parametrizable template."""
        config_path = self._global_config_path if global_config else self._local_config_path

        if config_path.exists() and not force:
            print(f"Config file already exists: {config_path}")
            print("Use --force to overwrite or edit the existing file.")
            return False

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            template_content = self._generate_config_template(
                is_global=global_config,
                comment_style=comment_style
            )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            config_type = "global" if global_config else "local"
            print(f"Configuration template created at: {config_path} ({config_type})")
            return True
        except OSError as e:
            print(f"Error creating config template at {config_path}: {e}")
            return False

    def get_config_path(self, global_config: bool = False) -> Path:
        """Get path to configuration file."""
        return self._global_config_path if global_config else self._local_config_path

    def show_config(self, global_config: bool | None = None) -> dict[str, Any]:
        """
        Show current configuration.

        Args:
            global_config: If True, show only global config. If False, only local.
                          If None, show merged configuration.
        """
        if global_config is True:
            # Show only global config
            if self._global_config_path.exists():
                with open(self._global_config_path, "r") as f:
                    return toml.load(f)
            return {}
        elif global_config is False:
            # Show only local config
            if self._local_config_path.exists():
                with open(self._local_config_path, "r") as f:
                    return toml.load(f)
            return {}
        else:
            # Show merged configuration
            return self._options.to_toml_dict()

    def reset_config(self, global_config: bool = False) -> bool:
        """Reset configuration file to defaults."""
        config_path = self._global_config_path if global_config else self._local_config_path

        if not config_path.exists():
            print(f"No config file exists at: {config_path}")
            return False

        try:
            # Create default options and save
            default_options = ConfigOptions()
            config_dict = default_options.to_toml_dict()
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
            print(f"Configuration reset to defaults: {config_path}")
            # Reload configs
            self.load_configs()
            return True
        except OSError as e:
            print(f"Error resetting config at {config_path}: {e}")
            return False

    def get_option(self, key: str, default: Any = None) -> Any:
        """Get configuration option value."""
        return getattr(self._options, key, default)

    def set_option(self, key: str, value: Any, propagate: bool = True) -> None:
        """
        Set configuration option and optionally propagate changes.

        Args:
            key: Option name
            value: Option value
            propagate: Whether to propagate changes to affected subsystems
        """
        if hasattr(self._options, key):
            setattr(self._options, key, value)
            if propagate:
                self._propagate_changes(key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    def _propagate_changes(self, key: str, value: Any) -> None:
        """Propagate configuration changes to affected subsystems."""
        # Language changes affect both Pint and LocalizationManager
        if key == "language" and value is not None:
            self._update_pint_language(value)
            self._update_localization_language(value)

        # Pint format changes
        elif key == "pint_default_format":
            self._update_pint_format(value)

        # SymPy printing options
        elif key == "default_mul_symbol":
            self._update_sympy_printing()

    def _update_pint_language(self, language: str) -> None:
        """Update Pint locale based on language setting."""
        # Check if Pint locale is disabled
        if self._options.disable_pint_locale:
            return

        try:
            from .pint_sympy import update_pint_locale
            update_pint_locale(language)
        except ImportError:
            pass  # Module not available

    def _update_localization_language(self, language: str) -> None:
        """Update LocalizationManager language."""
        try:
            from .localization import set_language
            set_language(language)
        except ImportError:
            pass  # Module not available

    def _update_pint_format(self, format_str: str) -> None:
        """Update Pint default format."""
        try:
            from .pint_sympy import u
            u.formatter.default_format = format_str
        except ImportError:
            pass  # Module not available

    def _update_sympy_printing(self) -> None:
        """Update SymPy printing settings."""
        try:
            import sympy as sp
            sp.init_printing(mul_symbol=self._options.default_mul_symbol, order="none")
        except ImportError:
            pass  # Module not available

    @property
    def options(self) -> ConfigOptions:
        """Get current configuration options."""
        return self._options

    def get_loaded_files(self) -> list:
        """Get list of successfully loaded configuration files."""
        return self._loaded_files.copy()

    def _generate_config_template(self, is_global: bool = True, comment_style: str = "##") -> str:
        """Generate a clean, parametrizable configuration template."""
        defaults = ConfigOptions()

        # Load global config values if this is a local config
        global_values = {}
        if not is_global and self._global_config_path.exists():
            try:
                with open(self._global_config_path, "r", encoding="utf-8") as f:
                    global_data = toml.load(f)
                    temp_config = ConfigOptions()
                    temp_config.update_from_dict(global_data)
                    global_values = temp_config.to_toml_dict()
            except Exception:
                pass  # Use defaults if global config can't be loaded

        config_type = "Global" if is_global else "Local"
        config_scope = "user-wide" if is_global else "project-specific"

        # Helper function to format values
        def format_value(section_name, key, default_val, inherited_val=None):
            # Special handling for None values
            if default_val is None and (inherited_val is None or not is_global):
                # Generate commented example for None default
                example_values = {
                    'default_float_format': '".3f"',  # Example format spec
                }
                example = example_values.get(key, '""')
                return f'# {key} = {example}'

            if is_global:
                # Global config: all values active
                toml_line = toml.dumps({key: default_val}).strip()
                return toml_line if toml_line else f'# {key} = ""'
            else:
                # Local config: show inherited values but commented with # for easy toggle
                display_val = inherited_val if inherited_val is not None else default_val
                toml_line = toml.dumps({key: display_val}).strip()
                return f'# {toml_line}' if toml_line else f'# {key} = ""'

        # Helper function to format template strings as TOML literal strings
        def format_template(template_str, comment=False):
            # Use literal string format (single quotes) for TOML
            formatted = f"'{template_str}'"
            return f"# {formatted}" if comment else formatted

        # Helper function to format template assignment lines
        def format_template_line(key, template_str, comment=False):
            formatted_template = f"'{template_str}'"
            if comment:
                return f"# {key} = {formatted_template}"
            else:
                return f"{key} = {formatted_template}"

        # Extract inherited values for local config
        latex_inherited = global_values.get('latex', {})
        display_inherited = global_values.get('display', {})
        language_inherited = global_values.get('language', {})
        units_inherited = global_values.get('units', {})
        translations_inherited = global_values.get('translations', {})
        check_templates_inherited = global_values.get('check_templates', {})

        template = f'''# Keecas {config_type} Configuration
# {"=" * (len(config_type) + 30)}
## {config_scope.capitalize()} settings for keecas symbolic math calculations
## Remove '#' to activate settings (local configs inherit from global)

[latex]
## LaTeX equation generation
{format_value("latex", "eq_prefix", defaults.latex.eq_prefix, latex_inherited.get("eq_prefix"))}
{format_value("latex", "eq_suffix", defaults.latex.eq_suffix, latex_inherited.get("eq_suffix"))}
{format_value("latex", "vertical_skip", defaults.latex.vertical_skip, latex_inherited.get("vertical_skip"))}
{format_value("latex", "default_environment", defaults.latex.default_environment, latex_inherited.get("default_environment"))}
{format_value("latex", "default_label_command", defaults.latex.default_label_command, latex_inherited.get("default_label_command"))}
{format_value("latex", "default_mul_symbol", defaults.latex.default_mul_symbol, latex_inherited.get("default_mul_symbol"))}

## LaTeX Environments
## Customize built-in environments or define new ones
## Built-in environments: {", ".join(sorted(defaults.latex.environments.keys()))}
##
## Example custom environment:
## [latex.environments.custom]
## separator = "&"
## line_separator = " \\\\\\n "
## supports_multiple_labels = true
## outer_environment = "align"
## inner_environment = ""  # Optional nested environment
## inner_prefix = ""       # Text before inner environment
## inner_suffix = ""       # Text after inner environment
## outer_prefix = ""       # Text before outer environment
## outer_suffix = ""       # Text after outer environment
## label_position = "outer"  # Where to place labels: "outer" or "inner"

[display]
## Display and debugging
{format_value("display", "print_label", defaults.display.print_label, display_inherited.get("print_label"))}
{format_value("display", "debug", defaults.display.debug, display_inherited.get("debug"))}
{format_value("display", "katex", defaults.display.katex, display_inherited.get("katex"))}

## Float formatting (Python format spec: .2f, .3f, .2e, etc.)
## Set default format for numeric values in equations
{format_value("display", "default_float_format", defaults.display.default_float_format, display_inherited.get("default_float_format"))}

[language]
## Language settings (de, es, fr, it, pt, da, nl, no, sv, en)
{format_value("language", "language", "en", language_inherited.get("language")) if is_global or language_inherited.get("language") else '# language = "en"'}
{format_value("language", "disable_pint_locale", defaults.language_config.disable_pint_locale, language_inherited.get("disable_pint_locale"))}

[units]
## Pint quantity formatting
{format_value("units", "pint_default_format", defaults.units.pint_default_format, units_inherited.get("pint_default_format"))}

[translations]
## Custom mathematical terms (e.g., "VERIFIED" = "VERIFICATO")
{"## Inherited from global config" if not is_global and translations_inherited else "## Add custom translations here"}

[check_templates]
## Check function templates (use literal strings 'string' for LaTeX)
{format_template_line("success_template", defaults.check_templates.success_template, comment=(not is_global and not check_templates_inherited.get("success_template")))}
{format_template_line("failure_template", defaults.check_templates.failure_template, comment=(not is_global and not check_templates_inherited.get("failure_template")))}

## Named template sets
{f"[check_templates.template_sets.default]" if is_global else "# [check_templates.template_sets.default]"}
{format_template_line("success", defaults.check_templates.template_sets['default']['success'], comment=not is_global)}
{format_template_line("failure", defaults.check_templates.template_sets['default']['failure'], comment=not is_global)}

{f"[check_templates.template_sets.boxed]" if is_global else "# [check_templates.template_sets.boxed]"}
{format_template_line("success", defaults.check_templates.template_sets['boxed']['success'], comment=not is_global)}
{format_template_line("failure", defaults.check_templates.template_sets['boxed']['failure'], comment=not is_global)}

{f"[check_templates.template_sets.minimal]" if is_global else "# [check_templates.template_sets.minimal]"}
{format_template_line("success", defaults.check_templates.template_sets['minimal']['success'], comment=not is_global)}
{format_template_line("failure", defaults.check_templates.template_sets['minimal']['failure'], comment=not is_global)}
'''

        # Add inherited custom translations for local config
        if not is_global and translations_inherited:
            for key, value in translations_inherited.items():
                template += f'# "{key}" = "{value}"\n'

        return template


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager


def get_options() -> ConfigOptions:
    """Get current configuration options (backward compatibility)."""
    return _config_manager.options


# Create backward-compatible options instance and new config alias
options = _config_manager.options
config = _config_manager.options  # New 1:1 mapping with config files