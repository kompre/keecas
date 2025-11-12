"""Unified Configuration Management for Keecas.

Manages all configuration options with TOML file support, hierarchical priority,
and dynamic propagation to affected subsystems (Pint locale, localization).

The main configuration object is exposed as `config` from the keecas package:

```{python}
from keecas import config

# Access nested configuration
config.language.language = 'it'                 # Italian localization
config.latex.eq_prefix = 'eq-'                  # LaTeX label prefix
config.display.default_float_format = '.3f'    # Default float formatting
config.display.katex = True                     # KaTeX compatibility mode

# Environment configuration
config.latex.environments.align.separator       # Built-in environment separator
config.latex.environments.set('custom', {...})  # Custom environment
```

```python
# Save configuration
from keecas.config import get_config_manager
manager = get_config_manager()
manager.save_config()  # Save to .keecas/config.toml
```

## Configuration Hierarchy

Priority order: Local config > Global config > Defaults

- **Local**: `<project>/.keecas/config.toml` (project-specific)
- **Global**: `~/.keecas/config.toml` (user-wide)
- **Defaults**: Built-in defaults in dataclass definitions

## Configuration Sections

- `config.latex`: LaTeX equation formatting (eq_prefix, environments, etc.)
- `config.display`: Display behavior (katex, debug, float_format, etc.)
- `config.language`: Language and localization (language, disable_pint_locale)
- `config.translations`: Custom term translations
- `config.check_templates`: Verification function templates

## Dynamic Propagation

Changes to certain settings automatically propagate:

- `config.language`: Updates Pint locale and localization manager
- Configuration changes trigger affected subsystem updates

See Also:
    - LatexConfig: LaTeX equation formatting configuration
    - DisplayConfig: Display and debugging configuration
    - LanguageConfig: Language and localization configuration
    - ConfigManager: Main configuration manager class
"""

import os
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
import tomlkit


@dataclass
class LatexConfig:
    """LaTeX equation output configuration."""

    eq_prefix: str = "eq-"
    eq_suffix: str = ""
    vertical_skip: str = "8pt"
    default_environment: str = "align"
    default_label_command: str = r"\label"
    default_mul_symbol: str = r"\,"
    label: "Callable | None" = (
        None  # Runtime-only: default label generator (not serializable to TOML)
    )
    environments: "EnvironmentConfig" = field(default_factory=lambda: None)

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
    pint_default_format: str = ".2f~P"
    cell_formatter: "Callable[[Any, int], str] | None" = None  # Custom cell formatter
    row_formatter: "Callable[[str], str] | None" = None  # Custom row formatter
    col_wrap: "list | Callable | None" = None  # Column wrapping specification


@dataclass
class LanguageConfig:
    """Language and localization configuration."""

    _language: str | None = field(default=None, init=False)
    disable_pint_locale: bool = True  # Disable by default to preserve compact unit symbols
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
        if hasattr(self, "_config_manager_ref"):
            self._config_manager_ref._propagate_changes("language", value)


@dataclass
class UnitsConfig:
    """Units formatting configuration."""

    pass


@dataclass
class TranslationsConfig:
    """Custom term translations configuration."""

    translations: dict[str, str] = field(default_factory=dict)


@dataclass
class CheckTemplateConfig:
    """Check function template configuration."""

    success_template: str = (
        r"$\textcolor{{green}}{{\left[{symbol}{rhs}\quad \textbf{{{verified_text}}}\right]}}$"
    )
    failure_template: str = (
        r"$\textcolor{{red}}{{\left[{symbol}{rhs}\quad \textbf{{{not_verified_text}}}\right]}}$"
    )
    # Named template sets
    template_sets: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            "default": {
                "success": r"$\textcolor{{green}}{{\left[{symbol}{rhs}\quad \textbf{{{verified_text}}}\right]}}$",
                "failure": r"$\textcolor{{red}}{{\left[{symbol}{rhs}\quad \textbf{{{not_verified_text}}}\right]}}$",
            },
            "boxed": {
                "success": r"\colorbox{{green}}{{${symbol}{rhs} \; \checkmark \; \textbf{{{verified_text}}}$}}",
                "failure": r"\colorbox{{red}}{{${symbol}{rhs} \; \times \; \textbf{{{not_verified_text}}}$}}",
            },
            "minimal": {
                "success": r"${symbol}{rhs} \,\textcolor{{green}}{{\checkmark}}$",
                "failure": r"${symbol}{rhs} \,\textcolor{{red}}{{\times}}$",
            },
        },
    )


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
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentDefinition":
        """Create from dictionary, filtering unknown keys."""
        valid_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        # Convert empty string to None for inner_environment
        if "inner_environment" in filtered_data and filtered_data["inner_environment"] == "":
            filtered_data["inner_environment"] = None
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
            inner_environment=None,
        )

        # Standard equation environment
        self.equation = EnvironmentDefinition(
            separator="",
            line_separator="",
            supports_multiple_labels=False,
            outer_environment="equation",
            inner_environment=None,
        )

        # Standard gather environment
        self.gather = EnvironmentDefinition(
            separator="",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=True,
            outer_environment="gather",
            inner_environment=None,
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
            label_position="outer",
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
            label_position="outer",
        )

        # Special split environment - nested structure
        self.split = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=False,
            outer_environment="align",
            inner_environment="aligned",
            label_position="outer",
        )

        # alignat environment - requires argument for number of column pairs
        self.alignat = EnvironmentDefinition(
            separator="&",
            line_separator=r" \\" + "\n ",
            supports_multiple_labels=True,
            outer_environment="alignat",
            inner_environment=None,
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
    language: LanguageConfig = field(default_factory=LanguageConfig)
    units: UnitsConfig = field(default_factory=UnitsConfig)
    translations: TranslationsConfig = field(default_factory=TranslationsConfig)
    check_templates: CheckTemplateConfig = field(default_factory=CheckTemplateConfig)

    def __post_init__(self):
        """Set up cross-references for language propagation."""
        self.language._config_manager_ref = getattr(self, "_config_manager_ref", None)

    def to_toml_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for TOML serialization.

        Note: latex.label is intentionally excluded (runtime-only, not serializable).
        """
        data = {
            "latex": {
                "eq_prefix": self.latex.eq_prefix,
                "eq_suffix": self.latex.eq_suffix,
                "vertical_skip": self.latex.vertical_skip,
                "default_environment": self.latex.default_environment,
                "default_label_command": self.latex.default_label_command,
                "default_mul_symbol": self.latex.default_mul_symbol,
                # label is intentionally excluded (runtime-only callable)
                "environments": {
                    name: env.to_dict() for name, env in self.latex.environments.items()
                },
            },
            "display": {
                "print_label": self.display.print_label,
                "debug": self.display.debug,
                "katex": self.display.katex,
                "default_float_format": self.display.default_float_format,
                "pint_default_format": self.display.pint_default_format,
            },
            "language": {
                "disable_pint_locale": self.language.disable_pint_locale,
                "pint_language_mode": self.language.pint_language_mode,
            },
            "check_templates": {
                "success_template": self.check_templates.success_template,
                "failure_template": self.check_templates.failure_template,
                "template_sets": self.check_templates.template_sets,
            },
        }

        # Add language if set
        if self.language.language is not None:
            data["language"]["language"] = self.language.language

        # Add custom translations if any
        if self.translations.translations:
            data["translations"] = self.translations.translations

        return data

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update configuration from dictionary (loaded from TOML)."""
        for section_key, section_data in data.items():
            if section_key == "latex" and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if key == "environments" and isinstance(value, dict):
                        # Handle nested environments under latex
                        for env_name, env_config in value.items():
                            if isinstance(env_config, dict):
                                self.latex.environments.set(env_name, env_config)
                    elif hasattr(self.latex, key):
                        setattr(self.latex, key, value)
            elif section_key == "display" and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if hasattr(self.display, key):
                        setattr(self.display, key, value)
            elif section_key == "language" and isinstance(section_data, dict):
                # Process disable_pint_locale FIRST to prevent unwanted locale changes
                if "disable_pint_locale" in section_data:
                    self.language.disable_pint_locale = section_data["disable_pint_locale"]

                # Then process other language settings
                for key, value in section_data.items():
                    if key == "disable_pint_locale":
                        continue  # Already processed
                    elif key == "language":
                        # Use the property setter to trigger propagation
                        self.language.language = value
                    elif hasattr(self.language, key):
                        setattr(self.language, key, value)
            elif section_key == "units" and isinstance(section_data, dict):
                for key, value in section_data.items():
                    if hasattr(self.units, key):
                        setattr(self.units, key, value)
            elif section_key == "translations" and isinstance(section_data, dict):
                self.translations.translations.update(section_data)
            elif section_key == "check_templates" and isinstance(section_data, dict):
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
        """Initialize ConfigManager - always succeeds even with broken configs."""
        # Path setup - always works
        self._global_config_path = self._get_global_config_path()
        self._local_config_path = self._get_local_config_path()

        # State tracking
        self._configs_loaded = False
        self._load_error = None  # Store error for helpful messages
        self._loaded_files = []

        # Try to load configs, but don't fail if broken
        try:
            self._options = ConfigOptions()
            # Set back-reference for language propagation
            self._options._config_manager_ref = self
            self._options.language._config_manager_ref = self
            self.load_configs()
            self._configs_loaded = True
        except Exception as e:
            # Store error but continue - path-only operations still work
            self._load_error = e
            # Create minimal options for path-only operations
            self._options = ConfigOptions()
            self._options._config_manager_ref = self
            self._options.language._config_manager_ref = self

    def _ensure_loaded(self) -> None:
        """Ensure configs are loaded, raise helpful error if broken."""
        if self._load_error:
            raise RuntimeError(
                f"Configuration could not be loaded: {self._load_error}\n"
                f"To fix: keecas config init --force [--global|--local]",
            )
        if not self._configs_loaded:
            self.load_configs()
            self._configs_loaded = True

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
        """Load configurations from files in priority order with automatic migration."""
        self._loaded_files = []

        # Load global config first (lower priority)
        if self._global_config_path.exists():
            try:
                self._load_and_migrate_config(self._global_config_path)
                self._loaded_files.append(str(self._global_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load global config from {self._global_config_path}: {e}")

        # Load local config second (higher priority)
        if self._local_config_path.exists():
            try:
                self._load_and_migrate_config(self._local_config_path)
                self._loaded_files.append(str(self._local_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load local config from {self._local_config_path}: {e}")

    def _load_and_migrate_config(self, config_path: Path) -> None:
        """Load config with automatic migration if needed.

        Parameters
        ----------
        config_path : Path
            Path to configuration file
        """
        from .migration import ConfigMigration
        from .schema import get_current_schema_version

        # Extract metadata from header comments
        metadata = self._extract_metadata_from_comments(config_path)
        config_version = metadata.get("config_version", "0.1.0")
        current_version = get_current_schema_version()

        # Load actual config data - use tomlkit to preserve structure
        with open(config_path, encoding="utf-8") as f:
            toml_doc = tomlkit.load(f)
            config_data = dict(toml_doc)  # Convert to dict for migration

        # Check if migration needed
        if ConfigMigration.needs_migration(config_version, current_version):
            print(f"WARNING: Config migration required: {config_version} -> {current_version}")

            # Backup old config
            backup_path = config_path.with_suffix(".toml.backup")
            shutil.copy(config_path, backup_path)
            print(f"Backup created: {backup_path}")

            # Perform migration
            try:
                migrated_data = ConfigMigration.migrate(
                    config_data,
                    config_version,
                    current_version,
                )
                self._options.update_from_dict(migrated_data)

                # Save migrated config preserving structure and comments
                self._save_migrated_config(
                    config_path,
                    toml_doc,
                    migrated_data,
                    created_at=metadata.get("generated_at"),
                )
                print(f"SUCCESS: Config migrated successfully to {current_version}")

            except Exception as e:
                print(f"ERROR: Migration failed: {e}")
                print(f"   Restore from backup: {backup_path}")
                raise

        else:
            self._options.update_from_dict(config_data)

    @staticmethod
    def _extract_metadata_from_comments(config_path: Path) -> dict:
        """Extract version metadata from config file header comments.

        Parameters
        ----------
        config_path : Path
            Path to config file

        Returns
        -------
        dict
            Dictionary with metadata (config_version, keecas_version, etc.)
        """
        metadata = {
            "config_version": "0.1.0",  # Default for old configs without header
            "keecas_version": "unknown",
            "generated_at": None,
            "last_modified": None,
        }

        if not config_path.exists():
            return metadata

        with open(config_path, encoding="utf-8") as f:
            for line in f:
                if not line.startswith("#"):
                    break  # Stop at first non-comment line

                if "Schema version:" in line:
                    metadata["config_version"] = line.split(":", 1)[1].strip()
                elif "Generated by keecas v" in line:
                    metadata["keecas_version"] = line.split("v")[1].strip()
                elif "Created:" in line:
                    metadata["generated_at"] = line.split(":", 1)[1].strip()
                elif "Last updated:" in line:
                    metadata["last_modified"] = line.split(":", 1)[1].strip()

        return metadata

    def save_config(self, global_config: bool = False, force: bool = False) -> bool:
        """Save current configuration to file with version metadata.

        Parameters
        ----------
        global_config : bool, optional
            If True, save to global config file
        force : bool, optional
            If True, overwrite existing file

        Returns
        -------
        bool
            True if saved successfully, False otherwise
        """
        self._ensure_loaded()
        config_path = self._global_config_path if global_config else self._local_config_path

        if config_path.exists() and not force:
            print(f"Config file already exists: {config_path}")
            print("Use --force to overwrite or edit the existing file.")
            return False

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._save_config_file(config_path)
            print(f"Configuration saved to: {config_path}")
            return True
        except OSError as e:
            print(f"Error saving config to {config_path}: {e}")
            return False

    def _save_config_file(self, config_path: Path, created_at: str | None = None) -> None:
        """Save config with version metadata in header comments.

        Parameters
        ----------
        config_path : Path
            Path to save configuration file
        created_at : str | None, optional
            Optional creation timestamp (preserves during migration)
        """
        from ..version import __version__
        from .schema import get_current_schema_version

        config_dict = self._options.to_toml_dict()
        schema_version = get_current_schema_version()
        now = datetime.now().isoformat()

        # Determine creation timestamp
        if created_at is None:
            # Try to preserve existing creation time from file
            if config_path.exists():
                existing_metadata = self._extract_metadata_from_comments(config_path)
                created_at = existing_metadata.get("generated_at")
            # If still None, this is a new file
            if created_at is None:
                created_at = now

        # Write with header comments containing metadata
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"### Generated by keecas v{__version__}\n")
            f.write(f"### Schema version: {schema_version}\n")
            f.write(f"### Created: {created_at}\n")
            f.write(f"### Last updated: {now}\n\n")
            toml.dump(config_dict, f)

    def _save_migrated_config(
        self,
        config_path: Path,
        toml_doc: tomlkit.TOMLDocument,
        migrated_data: dict,
        created_at: str | None = None,
    ) -> None:
        """Save migrated config preserving comments and structure.

        Parameters
        ----------
        config_path : Path
            Path to save configuration file
        toml_doc : tomlkit.TOMLDocument
            Original tomlkit document (preserves comments)
        migrated_data : dict
            Migrated configuration data
        created_at : str | None, optional
            Optional creation timestamp
        """
        from ..version import __version__
        from .schema import get_current_schema_version

        schema_version = get_current_schema_version()
        now = datetime.now().isoformat()

        # Determine creation timestamp
        if created_at is None:
            created_at = now

        # Apply changes to tomlkit document (preserves comments)
        def update_toml_doc(doc, data):
            """Recursively update tomlkit document with migrated data."""
            for key, value in data.items():
                if isinstance(value, dict):
                    if key not in doc:
                        doc[key] = {}
                    update_toml_doc(doc[key], value)
                else:
                    doc[key] = value

        # Remove renamed/removed keys from original doc
        def remove_old_keys(doc, keys_to_remove):
            """Remove old keys that were migrated."""
            for key in list(keys_to_remove):
                if key in doc:
                    del doc[key]

        # Get keys that were transformed
        original_keys = set(dict(toml_doc).keys())
        migrated_keys = set(migrated_data.keys())

        # Remove top-level keys that no longer exist
        removed_keys = original_keys - migrated_keys
        remove_old_keys(toml_doc, removed_keys)

        # Update with migrated data
        update_toml_doc(toml_doc, migrated_data)

        # Write with version header
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"### Generated by keecas v{__version__}\n")
            f.write(f"### Schema version: {schema_version}\n")
            f.write(f"### Created: {created_at}\n")
            f.write(f"### Last updated: {now}\n\n")
            f.write(tomlkit.dumps(toml_doc))

    def init_config(
        self,
        global_config: bool = False,
        force: bool = False,
        comment_style: str = "##",
    ) -> bool:
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
                comment_style=comment_style,
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
        """Show current configuration.

        Parameters
        ----------
        global_config : bool | None, optional
            If True, show only global config. If False, only local.
            If None, show merged configuration.

        Returns
        -------
        dict[str, Any]
            Configuration dictionary
        """
        if global_config is True:
            # Show only global config
            if self._global_config_path.exists():
                with open(self._global_config_path) as f:
                    return toml.load(f)
            return {}
        elif global_config is False:
            # Show only local config
            if self._local_config_path.exists():
                with open(self._local_config_path) as f:
                    return toml.load(f)
            return {}
        else:
            # Show merged configuration - needs loaded config
            self._ensure_loaded()
            return self._options.to_toml_dict()

    def reset_config(self, global_config: bool = False) -> bool:
        """Reset configuration file to defaults with proper template and version header."""
        config_path = self._global_config_path if global_config else self._local_config_path

        if not config_path.exists():
            print(f"No config file exists at: {config_path}")
            return False

        try:
            # Generate fresh template with version header (same as init_config)
            template_content = self._generate_config_template(
                is_global=global_config,
                comment_style="##",
            )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"Configuration reset to defaults: {config_path}")
            # Reload configs
            self.load_configs()
            return True
        except OSError as e:
            print(f"Error resetting config at {config_path}: {e}")
            return False

    def get_option(self, key: str, default: Any = None) -> Any:
        """Get configuration option value."""
        self._ensure_loaded()
        return getattr(self._options, key, default)

    def set_option(self, key: str, value: Any, propagate: bool = True) -> None:
        """Set configuration option and optionally propagate changes.

        Parameters
        ----------
        key : str
            Option name
        value : Any
            Option value
        propagate : bool, optional
            Whether to propagate changes to affected subsystems
        """
        self._ensure_loaded()
        if hasattr(self._options, key):
            setattr(self._options, key, value)
            if propagate:
                self._propagate_changes(key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    def _propagate_changes(self, key: str, value: Any) -> None:
        """Propagate configuration changes to affected subsystems."""
        self._ensure_loaded()
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
        if self._options.language.disable_pint_locale:
            return

        try:
            from ..pint_sympy import update_pint_locale

            update_pint_locale(language)
        except ImportError:
            pass  # Module not available

    def _update_localization_language(self, language: str) -> None:
        """Update LocalizationManager language."""
        try:
            from ..localization import set_language

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
        """Generate a clean, parametrizable configuration template with version header."""
        from datetime import datetime

        from ..version import __version__
        from .schema import get_current_schema_version

        defaults = ConfigOptions()

        # Load global config values if this is a local config
        global_values = {}
        if not is_global and self._global_config_path.exists():
            try:
                with open(self._global_config_path, encoding="utf-8") as f:
                    global_data = toml.load(f)
                    temp_config = ConfigOptions()
                    temp_config.update_from_dict(global_data)
                    global_values = temp_config.to_toml_dict()
            except Exception:
                pass  # Use defaults if global config can't be loaded

        config_type = "Global" if is_global else "Local"
        config_scope = "user-wide" if is_global else "project-specific"

        # Generate version header
        schema_version = get_current_schema_version()
        now = datetime.now().isoformat()
        version_header = f"""### Generated by keecas v{__version__}
### Schema version: {schema_version}
### Created: {now}
### Last updated: {now}

"""

        # Helper function to format values
        def format_value(section_name, key, default_val, inherited_val=None):
            # Special handling for None values
            if default_val is None and (inherited_val is None or not is_global):
                # Generate commented example for None default
                example_values = {
                    "default_float_format": '".3f"',  # Example format spec
                }
                example = example_values.get(key, '""')
                return f"# {key} = {example}"

            # Both global and local configs: comment all values
            # Users uncomment what they want to change from defaults
            display_val = (
                inherited_val if (inherited_val is not None and not is_global) else default_val
            )
            toml_line = toml.dumps({key: display_val}).strip()
            return f"# {toml_line}" if toml_line else f'# {key} = ""'

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
        latex_inherited = global_values.get("latex", {})
        display_inherited = global_values.get("display", {})
        language_inherited = global_values.get("language", {})
        _units_inherited = global_values.get("units", {})  # Reserved for future use
        translations_inherited = global_values.get("translations", {})

        template = f"""### Keecas {config_type} Configuration
### {"=" * (len(config_type) + 30)}
### {config_scope.capitalize()} settings for keecas symbolic math calculations
### Remove '#' to activate settings (local configs inherit from global)

[latex]
## LaTeX equation generation
{format_value("latex", "eq_prefix", defaults.latex.eq_prefix, latex_inherited.get("eq_prefix"))}
{format_value("latex", "eq_suffix", defaults.latex.eq_suffix, latex_inherited.get("eq_suffix"))}
{format_value("latex", "vertical_skip", defaults.latex.vertical_skip, latex_inherited.get("vertical_skip"))}
{format_value("latex", "default_environment", defaults.latex.default_environment, latex_inherited.get("default_environment"))}
{format_value("latex", "default_label_command", defaults.latex.default_label_command, latex_inherited.get("default_label_command"))}
{format_value("latex", "default_mul_symbol", defaults.latex.default_mul_symbol, latex_inherited.get("default_mul_symbol"))}

## Default label generator (runtime-only, cannot be set in TOML)
## Set via Python: config.latex.label = callable or None
## When show_eqn(label=None), uses this default
## Example: config.latex.label = generate_stable_label

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

## Pint quantity formatting (e.g., .2f~P, .3f~P)
{format_value("display", "pint_default_format", defaults.display.pint_default_format, display_inherited.get("pint_default_format"))}

[language]
## Language settings (de, es, fr, it, pt, da, nl, no, sv, en)
## Note: When disable_pint_locale=true, language only affects keecas term translations (not Pint units)
{'# language = "en"' if is_global else ('# language = "en"' if not language_inherited.get("language") else format_value("language", "language", language_inherited.get("language"), None))}
{format_value("language", "disable_pint_locale", defaults.language.disable_pint_locale, language_inherited.get("disable_pint_locale"))}

[translations]
## Custom mathematical terms (e.g., "VERIFIED" = "VERIFICATO")
{"## Inherited from global config" if not is_global and translations_inherited else "## Add custom translations here"}

[check_templates]
## Check function templates (use literal strings 'string' for LaTeX)
## Top-level templates are used as default fallback when no named template specified
{format_template_line("success_template", defaults.check_templates.success_template, comment=True)}
{format_template_line("failure_template", defaults.check_templates.failure_template, comment=True)}

## Named template sets (alternative templates selectable via check(template="name"))
# [check_templates.template_sets.default]
{format_template_line("success", defaults.check_templates.template_sets["default"]["success"], comment=True)}
{format_template_line("failure", defaults.check_templates.template_sets["default"]["failure"], comment=True)}

# [check_templates.template_sets.boxed]
{format_template_line("success", defaults.check_templates.template_sets["boxed"]["success"], comment=True)}
{format_template_line("failure", defaults.check_templates.template_sets["boxed"]["failure"], comment=True)}

# [check_templates.template_sets.minimal]
{format_template_line("success", defaults.check_templates.template_sets["minimal"]["success"], comment=True)}
{format_template_line("failure", defaults.check_templates.template_sets["minimal"]["failure"], comment=True)}
"""

        # Add inherited custom translations for local config
        if not is_global and translations_inherited:
            for key, value in translations_inherited.items():
                template += f'# "{key}" = "{value}"\n'

        # Prepend version header
        return version_header + template


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
