# Planning Notes - Keecas Development

**Date**: 2025-09-22
**Session**: Next phase development planning
**Previous Work**: Archived in `.claude/archive/PLANNING-ARCHIVE-2025-09-22.md`

## Workflow
1. **Planning**: Add brief notes below
2. **Expansion**: Claude expands selected items into detailed plans; ask question for clarifications
3. **Approval**: Review and approve/modify plans
4. **Execution**: Claude implements approved plans with TodoWrite tracking

---

## Ideas/Tasks to Tackle

This section is written by the user.

### launch jupyter server with keecas templates

If possible I would like to launch the jupyter server with an already opened notebook, but without creating a saved file. I would prefer a temporary file, that the user should decide if it want to be saved or not. Many times a user need something on the fly, without tha hassle of dealing with file management. If it decide to actually save the work, it can always save it as a new file.

As a side, lower priority we should look on providing intellisense/autocomplete, otherwise it will be a bit of a chore to use. This feature is to implement only if it does not bloat our package. Having the ability to launch a jupyter server is a nice to have, not a must.

The templates should be shipped with the package (we're using uv_build).

---

## Expanded Plans (Ready for Execution)

This section is written by Claude.

User comments and and answers will be added here inside comment blocks <!-- comment by user -->

### 1. Check Function Templating - DETAILED PLAN

**Problem Analysis:**
Currently the `check()` function in `display.py:38-91` has hardcoded LaTeX templates:
- Success: `\textcolor{green}{\left[{symbol}{rhs}\quad \textbf{{verified_text}}\right]}`
- Failure: `\textcolor{red}{\left[{symbol}{rhs}\quad \textbf{{not_verified_text}}\right]}`

Users want customizable templates for different visual styles (e.g., green box with checkmark, red box with X).

**Current Check Function Behavior:**
- Takes `lhs`, `rhs`, `test` (comparison function), and kwargs
- Determines success/failure symbols based on test type (≤, <, ≥, >, =, ≠)
- Uses localized text for VERIFIED/NOT_VERIFIED
- Returns Markdown with colored LaTeX output

**Proposed Templating System:**

#### Phase 1: Template Configuration Structure
**Add template configuration to config system:**
- Create `CheckTemplateConfig` dataclass with template strings
- Add to main `ConfigOptions` class
- Support TOML configuration with reasonable defaults
- Templates should use placeholder variables: `{symbol}`, `{rhs}`, `{verified_text}`, `{color}`

**Template Structure:**
```toml
[check_templates]
success_template = "\\textcolor{{green}}{{\\left[{symbol}{rhs}\\quad \\textbf{{{verified_text}}}\\right]}}"
failure_template = "\\textcolor{{red}}{{\\left[{symbol}{rhs}\\quad \\textbf{{{not_verified_text}}}\\right]}}"

# Alternative box styles
# success_template = "\\colorbox{{green!20}}{{\\scriptsize $${symbol}{rhs}$$ \\checkmark \\textbf{{{verified_text}}}}}"
# failure_template = "\\colorbox{{red!20}}{{\\scriptsize $${symbol}{rhs}$$ \\times \\textbf{{{not_verified_text}}}}}"
```

#### Phase 2: Template Processing System
**Modify check function to use templates:**
- Extract template from config system (with backward compatibility)
- Create template formatter that handles variable substitution
- Support both simple string templates and function-based templates
- Maintain current symbol logic for different test types
- Preserve localization integration

**Template Variables Available:**
- `{symbol}`: Comparison symbol (≤, >, =, etc.)
- `{rhs}`: Right-hand side value
- `{verified_text}`: Localized "VERIFIED" text
- `{not_verified_text}`: Localized "NOT_VERIFIED" text
- `{color}`: Success/failure color ("green"/"red")
- `{test_result}`: Boolean result for conditional logic

#### Phase 3: Advanced Template Features
**Template inheritance and variants:**
- Named template sets (e.g., "default", "boxed", "minimal")
- Template inheritance from global to local configs
- Runtime template override via function parameters
- Template validation to ensure required variables

**Enhanced Template Options:**
```python
# Simple override
check(lhs=stress, rhs=1.0, template="boxed")

# Custom template
check(lhs=stress, rhs=1.0,
      success_template="\\fbox{{✓ ${symbol}{rhs}$ OK}}",
      failure_template="\\fbox{{✗ ${symbol}{rhs}$ FAIL}}")
```

#### Implementation Plan

**Files to Modify:**
- `src/keecas/config.py` - Add `CheckTemplateConfig` dataclass and integrate into `ConfigOptions`
- `src/keecas/display.py` - Modify `check()` function to use configurable templates
- Template config files - Add template examples to TOML config generation
- Tests - Add template functionality tests
- Documentation/examples - Show template customization examples

**Backward Compatibility:**
- Default templates preserve exact current output
- All existing `check()` calls continue working unchanged
- Template system is opt-in through configuration

#### Template Processing Logic
```python
def format_check_template(template: str, **variables) -> str:
    """Format template string with variable substitution."""
    return template.format(**variables)

def get_check_templates(template_name: str = None) -> Tuple[str, str]:
    """Get success/failure templates from config."""
    if template_name:
        # Look up named template set
        pass
    return config.check_templates.success_template, config.check_templates.failure_template
```

**Estimated Complexity:** Medium - requires config system extension and template processing logic, but check function changes are localized

---

## Completed This Session

### ✅ Check Function Templating System - COMPLETED

**Complete implementation of customizable check function templates with proper LaTeX rendering:**

✅ **Template Configuration System**
- Added `CheckTemplateConfig` dataclass with configurable success/failure templates
- Integrated into unified TOML configuration system with proper literal string support
- Pre-built template sets: "default" (classic brackets), "boxed" (colorbox with symbols), "minimal" (simple symbols)
- KaTeX-compatible LaTeX formatting with proper math delimiters

✅ **Enhanced API with IDE Autocomplete**
- Updated function signature: `check(lhs, rhs, test=Le, template=..., success_template=..., failure_template=...)`
- Added `TemplateChoice = Literal["default", "boxed", "minimal"]` for IDE autocomplete
- Explicit parameters with full backward compatibility for kwargs usage
- Rich template variable substitution: `{symbol}`, `{rhs}`, `{verified_text}`, `{color}`, etc.

✅ **Configuration File Generation**
- TOML literal strings for clean LaTeX (no escaped backslashes)
- Global config: Active template definitions with all named template sets
- Local config: Commented templates for easy inheritance and customization
- Proper CLI config management integration

✅ **Template Examples and Documentation**
- Updated Quarto example notebook with template demonstrations
- All three template styles showcased with success/failure cases
- Template configuration examples and best practices

**Key Achievements:**
- **🎯 IDE Autocomplete**: Template parameter shows "default", "boxed", "minimal" options
- **📝 Clean LaTeX**: Literal strings in TOML with no escaped backslashes
- **🎨 Visual Variety**: Multiple template styles from classic brackets to modern colorboxes
- **🔧 Easy Customization**: TOML config files with clear template structure
- **🔄 Backward Compatible**: All existing check() calls continue to work unchanged
- **🧪 Fully Tested**: 10 comprehensive template tests, all 82 tests passing

**Usage Examples:**
```python
# Named templates with IDE autocomplete
check(0.8, 1.0, template="boxed")    # Colorbox with checkmark/X
check(0.8, 1.0, template="minimal")  # Simple symbols only

# Custom templates
check(0.8, 1.0,
      success_template="✅ {symbol}{rhs} PASS",
      failure_template="❌ {symbol}{rhs} FAIL")

# TOML configuration (literal strings)
[check_templates.template_sets.custom]
success = '\colorbox{blue}{${symbol}{rhs} \; \checkmark$}'
failure = '\colorbox{orange}{${symbol}{rhs} \; \times$}'
```

**Final Template Formats (KaTeX-Compatible):**
- **Default:** `$\textcolor{green}{\left[\le1.0\quad \textbf{VERIFIED}\right]}$`
- **Boxed:** `\colorbox{green}{$\le1.0 \; \checkmark \; \textbf{VERIFIED}$}`
- **Minimal:** `$\le1.0 \,\textcolor{green}{\checkmark}$`

The templating system enables complete visual customization while maintaining mathematical accuracy and proper LaTeX rendering!

### ✅ Check Function Template Enhancements - COMPLETED

**Complete implementation of template improvements and bug fixes:**

✅ **Fixed Failing Unit Tests**
- Updated `test_check_template_boxed()` to match new boxed template format
- Fixed `test_check_template_minimal()` for proper assertions
- All template tests passing

✅ **Enhanced Function Signature with IDE Support**
- Added `TemplateChoice = Literal["default", "boxed", "minimal"]` for IDE autocomplete
- Made template parameters explicit: `template`, `success_template`, `failure_template`
- Full backward compatibility with kwargs maintained

✅ **Fixed LaTeX Math Rendering**
- **Corrected Math Delimiters**: Templates now use single `$` for inline math instead of `$$`
- **Fixed KaTeX Compatibility**: `\colorbox{}` properly wraps math content, not wrapped by math
- **Proper Template Format**:
  - Default/Minimal: `$\textcolor{green}{\left[...\right]}$`
  - Boxed: `\colorbox{green}{$...$}` (KaTeX-safe)

✅ **Enhanced Config File Generation**
- **True Literal Strings**: TOML configs use clean `'$\textcolor{green}{...'` format
- **No Escaped Backslashes**: LaTeX commands readable in config files
- **Complete Template Sets**: All three template sets included in generated configs
- **Proper Local Config**: Template values correctly commented for inheritance

**Final Template Examples:**
```toml
[check_templates]
success_template = '$\textcolor{green}{\left[{symbol}{rhs}\quad \textbf{{verified_text}}\right]}$'

[check_templates.template_sets.boxed]
success = '\colorbox{green}{${symbol}{rhs} \; \checkmark \; \textbf{{verified_text}}$}'

[check_templates.template_sets.minimal]
success = '${symbol}{rhs} \,\textcolor{green}{\checkmark}$'
```

**Key Achievements:**
- **🎯 Perfect LaTeX Rendering**: Inline math with proper delimiters
- **⚡ IDE Autocomplete**: Template parameter suggestions
- **📝 Clean Config Files**: Readable literal strings for LaTeX
- **🔄 Full Compatibility**: All existing code works unchanged
- **✅ Comprehensive Testing**: 82/82 tests passing

The check function templating system is now production-ready with proper LaTeX rendering, clean configuration, and excellent developer experience!

### ✅ Localization System Integration - COMPLETED

**Complete architectural refactor and integration:**

✅ **Localization System Simplification** - Replaced complex LocalizationManager with simple functions
✅ **Configuration System Unification** - Eliminated duplicate config systems, fixed file paths
✅ **Project Metadata & Dynamic URLs** - Added proper project URLs and dynamic GitHub URL handling
✅ **Language Files Cleanup & Testing** - Removed deprecated entries, standardized structure, added comprehensive tests
✅ **Code Reduction** - Removed ~200 lines and 2 entire files of unnecessary code

**Key achievements:**
- All 72 tests passing (added 10 new structure validation tests)
- Clean, maintainable codebase with simplified architecture
- Smart pint locale detection respecting user manual changes
- Proper integration with main configuration system
- Standards-compliant project metadata

### ✅ Pre-commit Hook Fix - COMPLETED

✅ **Fixed hook scope** - Now only processes notebooks in `examples/.*quarto.*/` directories
✅ **Cleaned up tracking** - Removed hello_world generated files that shouldn't be tracked
✅ **Verified behavior** - hello_world.ipynb changes are ignored, quarto_example notebooks are processed

**Result:** Pre-commit hook now correctly distinguishes between simple examples and full quarto demonstrations.

---

## Archive Reference

Previous completed work has been moved to `.claude/archive/PLANNING-ARCHIVE-2025-09-22.md` including:
- Complete localization module refactor (3 phases)
- Configuration system cleanup and unification
- Project metadata and dynamic URL implementation
- Language files standardization and testing
- Pre-commit hook automation system

The codebase is now clean, well-tested, and ready for the next phase of development focusing on user experience improvements and templating features.