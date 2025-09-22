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

This section is written by the user. Empty after completion of task.

---

## Completed This Session

### ✅ Jupyter Server with Keecas Templates - COMPLETED

**Complete implementation of enhanced `keecas edit` command with default template behavior:**

✅ **Default Template Behavior**
- `keecas edit` now automatically creates minimal template and launches JupyterLab
- Users can start coding immediately without specifying template or flags
- JupyterLab is now the default interface (with graceful fallback to classic Jupyter)

✅ **Enhanced Template System**
- Created `minimal.ipynb` template as default (basic keecas setup)
- Existing `quickstart.ipynb` available for comprehensive examples
- Template listing with `keecas edit --list-templates`

✅ **Temporary Notebook Support**
- `--temp` flag creates notebooks in system temp directories
- Automatic cleanup when server stops (Ctrl+C)
- Jupyter auto-saves work in temp directory, user can manually save elsewhere

✅ **Enhanced CLI Interface**
- `--no-lab` option to use classic Jupyter instead of JupyterLab
- `--list-templates` shows available templates with descriptions
- Clear status messages indicating temporary vs permanent sessions

**Key Features Implemented:**
```bash
# Basic usage - minimal template in JupyterLab
keecas edit

# Temporary session with auto-cleanup
keecas edit --temp

# Use comprehensive examples
keecas edit --template quickstart

# List available templates
keecas edit --list-templates

# Use classic Jupyter instead of JupyterLab
keecas edit --no-lab
```

**Files Modified:**
- `src/keecas/cli.py` - Enhanced edit command with default template and temp support
- `templates/minimal.ipynb` - New minimal template for default usage

**Backward Compatibility:**
- All existing `keecas edit` commands work unchanged
- New features are additive, no breaking changes

**Key Achievements:**
- **🚀 Zero-Config Start**: `keecas edit` immediately launches ready-to-use notebook
- **🗂️ Smart Defaults**: Minimal template with JupyterLab for best user experience
- **⏱️ Temporary Sessions**: Auto-cleanup for quick calculations
- **📋 Template Discovery**: Easy template listing and selection
- **🔄 Full Compatibility**: No breaking changes to existing workflows
- **✅ Comprehensive Testing**: All 82 tests passing

The enhanced `keecas edit` command now provides the streamlined "on the fly" calculation experience requested by the user!

### ✅ File Argument Support - COMPLETED

**Complete implementation of file-based notebook opening and creation:**

✅ **File Argument Support**
- `keecas edit <file.ipynb>` opens existing files or creates new ones
- Positional file argument is optional (maintains current behavior)
- Smart handling of existing vs new files

✅ **Untitled File Naming**
- Default behavior creates `untitled-1.ipynb`, `untitled-2.ipynb`, etc.
- Automatic conflict resolution with incremental numbering
- Clean naming convention following standard practices

✅ **File Handling Logic**
- **Existing files**: Opens directly without template processing
- **New files**: Creates from template (default: minimal) with specified name
- **No file specified**: Creates with auto-generated untitled-N.ipynb name

**Key Usage Patterns:**
```bash
# Open or create specific file
keecas edit analysis.ipynb          # Creates analysis.ipynb from minimal template
keecas edit existing.ipynb          # Opens existing.ipynb directly

# Auto-generated names
keecas edit                         # Creates untitled-1.ipynb
keecas edit --template quickstart   # Creates untitled-N.ipynb from quickstart

# Combined with other features
keecas edit report.ipynb --temp     # Creates temporary report.ipynb
keecas edit --no-lab analysis.ipynb # Opens in classic Jupyter
```

**Functions Implemented:**
- `generate_untitled_name(work_dir)` - Conflict-free untitled naming
- Enhanced `copy_template_to_workdir()` with target filename support
- Smart file existence detection and handling

**Files Modified:**
- `src/keecas/cli.py` - File argument parsing and handling logic

**Key Achievements:**
- **📁 Flexible File Handling**: Open existing or create new files by name
- **🔢 Smart Naming**: Automatic untitled-N.ipynb with conflict resolution
- **🎯 User-Friendly**: Intuitive file-based workflow
- **🔄 Full Compatibility**: All existing commands work unchanged
- **✅ Comprehensive Testing**: All 82 tests passing, core functions validated

The file support implementation delivers exactly the requested functionality for opening specific files and creating untitled notebooks with proper naming!

### ✅ Automatic File Opening - COMPLETED

**Complete implementation of native Jupyter file auto-opening:**

✅ **Native Jupyter Integration**
- Used `--ServerApp.file_to_run` parameter for direct file opening
- Eliminates complex workspace URL detection and construction
- Works reliably across all Jupyter versions and platforms

✅ **Simplified Command Construction**
- Added file parameter to Jupyter launch command automatically
- Uses relative path from working directory for proper file resolution
- Works for both JupyterLab and classic Jupyter Notebook

✅ **Streamlined URL Handling**
- Removed complex URL construction logic (workspace detection, manual opening)
- Jupyter handles file opening natively at launch
- Cleaner, more maintainable code

**Technical Implementation:**
```python
# Enhanced Jupyter command construction:
if notebook_path:
    relative_path = notebook_path.relative_to(work_dir)
    jupyter_cmd.extend(['--ServerApp.file_to_run', str(relative_path)])
```

**Key Usage Examples:**
```bash
# Now automatically opens files in Jupyter:
keecas edit analysis.ipynb          # Creates & opens analysis.ipynb
keecas edit existing.ipynb          # Opens existing.ipynb directly
keecas edit --temp analysis.ipynb   # Creates temporary analysis.ipynb & opens it
```

**Files Modified:**
- `src/keecas/cli.py` - Added `--ServerApp.file_to_run` parameter, simplified URL handling

**Key Achievements:**
- **🎯 Native Integration**: Uses Jupyter's built-in file opening capability
- **🚀 Instant Opening**: Files open automatically without manual navigation
- **🔧 Simplified Code**: Removed 20+ lines of complex URL construction
- **🔄 Universal Compatibility**: Works with all Jupyter interfaces and versions
- **✅ Robust Testing**: All 82 tests passing, functionality validated

The auto-open implementation provides seamless file opening using Jupyter's native capabilities, delivering exactly the requested user experience!

---

**Previous completed work archived to:** `.claude/archive/COMPLETED-ARCHIVE-2025-09-22.md`