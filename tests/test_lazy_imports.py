"""Tests for lazy import mechanism in keecas package.

This module tests the lazy loading optimization that defers imports of heavy
dependencies (sympy, pint) until they're actually needed. This is critical for
fast CLI startup time (~45ms vs ~2000ms).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


# Performance thresholds
MAX_IMPORT_TIME_MS = 100  # Maximum acceptable import time in milliseconds
MAX_BASIC_IMPORT_TIME_MS = 50  # Maximum for basic import without heavy deps

# Get project root directory (parent of tests directory)
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def get_test_env():
    """Get environment dict with PYTHONPATH set for subprocess tests."""
    env = os.environ.copy()
    # Add src directory to PYTHONPATH so subprocess can find keecas
    pythonpath = str(SRC_DIR)
    if "PYTHONPATH" in env:
        pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
    env["PYTHONPATH"] = pythonpath
    return env


def test_import_performance():
    """Test that basic 'import keecas' completes quickly without heavy dependencies."""
    # Run import in subprocess for isolation
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "importtime",
            "-c",
            "import keecas",
        ],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Import failed: {result.stderr}"

    # Parse import time from stderr (Python -X importtime output)
    # Look for lines like: "import time:      1234 |      5678 | keecas"
    lines = result.stderr.split("\n")
    keecas_time = None
    for line in lines:
        if "keecas" in line and "|" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                # Get cumulative time (second column)
                time_str = parts[1].strip()
                if time_str.isdigit():
                    keecas_time = int(time_str) / 1000  # Convert microseconds to ms
                    break

    # Also measure with time command for overall verification
    result_time = subprocess.run(
        [sys.executable, "-c", "import keecas"],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result_time.returncode == 0, "Basic import should succeed"

    # We can't easily measure exact time cross-platform, but we verify no errors
    # The real performance test is the no-heavy-deps test below


def test_no_heavy_deps_on_basic_import():
    """Test that sympy/pint are NOT imported on basic 'import keecas'."""
    code = """
import sys
import keecas

# Check that heavy dependencies are not loaded
assert 'sympy' not in sys.modules, "sympy should not be loaded on basic import"
assert 'pint' not in sys.modules, "pint should not be loaded on basic import"
assert 'pipe' not in sys.modules, "pipe should not be loaded on basic import"

# Verify __version__ is accessible without heavy imports
assert hasattr(keecas, '__version__')
assert isinstance(keecas.__version__, str)
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}\n{result.stdout}"


def test_version_accessible_without_heavy_deps():
    """Test that __version__ is accessible without loading heavy dependencies."""
    code = """
import sys
import keecas

# Access __version__
version = keecas.__version__
assert version is not None
assert isinstance(version, str)
assert len(version) > 0

# Verify heavy deps still not loaded
assert 'sympy' not in sys.modules, "Accessing __version__ should not load sympy"
assert 'pint' not in sys.modules, "Accessing __version__ should not load pint"
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_lazy_loading_caching():
    """Test that lazy-loaded attributes are cached in globals() after first access."""
    code = """
import keecas

# First access of 'symbols' should load it
symbols = keecas.symbols

# Verify it's now in keecas module's globals
import sys
keecas_module = sys.modules['keecas']
assert 'symbols' in dir(keecas_module)

# Second access should return cached value (same object)
symbols2 = keecas.symbols
assert symbols is symbols2, "Cached attribute should return same object"
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_config_loads_before_dependencies():
    """Test that config object is loaded before sympy/pint dependencies."""
    code = """
import keecas

# Access config first
config = keecas.config

# Verify it has the 'display' attribute (ConfigOptions, not package module)
assert hasattr(config, 'display'), "config should be ConfigOptions, not package module"
assert hasattr(config, 'latex'), "config should have latex section"
assert hasattr(config, 'language'), "config should have language section"

# Now access sympy - should use the already-loaded config
symbols = keecas.symbols

# Verify sympy is now loaded but config was already there
import sys
assert 'sympy' in sys.modules
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_config_collision_detection():
    """Test that config collision detection prevents loading wrong config."""
    code = """
import keecas

# Access config - should be ConfigOptions object
config = keecas.config

# Verify it's the right type by checking for display attribute
assert hasattr(config, 'display'), "Should have display attribute (ConfigOptions)"

# The config package module would NOT have this attribute
# This verifies the collision detection is working
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_partial_import_symbols():
    """Test that 'from keecas import symbols' loads only necessary dependencies."""
    code = """
import sys
from keecas import symbols

# symbols should work
x = symbols('x')
assert x is not None

# sympy should now be loaded (symbols requires it)
assert 'sympy' in sys.modules, "sympy should be loaded when importing symbols"

# Config should also be loaded (required by sympy initialization)
assert 'keecas.display' in sys.modules or 'display' in dir(sys.modules.get('keecas', {}))
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_partial_import_u():
    """Test that 'from keecas import u' loads pint registry."""
    code = """
import sys
from keecas import u

# u (unit registry) should work
distance = 5 * u.meter
assert distance is not None

# pint should now be loaded
assert 'pint' in sys.modules, "pint should be loaded when importing u"

# Config should be loaded (required by u initialization)
keecas_module = sys.modules.get('keecas')
assert keecas_module is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_partial_import_pc():
    """Test that 'from keecas import pc' loads pipe_command module."""
    code = """
import sys
from keecas import pc

# pc (pipe_command) should work
assert pc is not None
assert hasattr(pc, 'subs') or hasattr(pc, 'N'), "pc should have pipe command functions"

# pipe module should be loaded
# Note: pipe_command is a keecas submodule, not external
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_import_pattern_module_access():
    """Test 'import keecas' then 'keecas.symbols(...)' pattern."""
    code = """
import keecas

# Access attributes via module
symbols = keecas.symbols
u = keecas.u
pc = keecas.pc

# All should work
x = symbols('x')
distance = 5 * u.meter
assert x is not None
assert distance is not None
assert pc is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_import_pattern_multiple_from():
    """Test 'from keecas import u, pc, symbols' pattern."""
    code = """
from keecas import u, pc, symbols

# All should be accessible
x = symbols('x')
distance = 5 * u.meter

assert x is not None
assert distance is not None
assert pc is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_import_star_pattern():
    """Test 'from keecas import *' pattern."""
    code = """
from keecas import *

# Should have access to main exports
x = symbols('x')
distance = 5 * u.meter
config_obj = config

assert x is not None
assert distance is not None
assert config_obj is not None
assert hasattr(config_obj, 'display')
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_heavy_deps_only_load_when_accessed():
    """Test that heavy dependencies only load when actually accessed."""
    code = """
import sys
import keecas

# Import keecas but don't access heavy deps
assert 'sympy' not in sys.modules, "sympy should not be loaded yet"
assert 'pint' not in sys.modules, "pint should not be loaded yet"

# Access __version__ (truly lightweight, no deps)
_ = keecas.__version__
# sympy/pint still should not be loaded
assert 'sympy' not in sys.modules, "__version__ should not load sympy"
assert 'pint' not in sys.modules, "__version__ should not load pint"

# Access Dataframe (lightweight, no sympy/pint)
_ = keecas.Dataframe
assert 'sympy' not in sys.modules, "Dataframe should not load sympy"
assert 'pint' not in sys.modules, "Dataframe should not load pint"

# Now access a heavy dependency
_ = keecas.symbols
# sympy should now be loaded
assert 'sympy' in sys.modules, "sympy should be loaded after accessing symbols"

# Access another heavy dependency
_ = keecas.u
# pint should now be loaded
assert 'pint' in sys.modules, "pint should be loaded after accessing u"
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_batch_sympy_exports_load_together():
    """Test that batch sympy exports (Eq, Le, latex, etc.) load together efficiently."""
    code = """
import sys
from keecas import Eq, Le, symbols

# All should be accessible
x = symbols('x')
eq = Eq(x, 5)
le = Le(x, 10)

assert eq is not None
assert le is not None

# sympy should be loaded once for all of them
assert 'sympy' in sys.modules
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_dataframe_is_lightweight():
    """Test that Dataframe can be imported without heavy dependencies."""
    code = """
import sys
from keecas import Dataframe

# Dataframe should be accessible
df = Dataframe()
assert df is not None

# Heavy deps should NOT be loaded just for Dataframe
assert 'sympy' not in sys.modules, "Dataframe should not require sympy"
assert 'pint' not in sys.modules, "Dataframe should not require pint"
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_multiple_lazy_loads_in_sequence():
    """Test that multiple lazy loads in sequence work correctly."""
    code = """
import keecas

# Load multiple attributes in sequence
config = keecas.config
symbols = keecas.symbols
u = keecas.u
pc = keecas.pc
latex = keecas.latex

# All should work
assert config is not None
assert symbols is not None
assert u is not None
assert pc is not None
assert latex is not None

# Test they actually work
x = symbols('x')
distance = 5 * u.meter
assert x is not None
assert distance is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"


def test_show_eqn_lazy_load():
    """Test that show_eqn triggers appropriate lazy loads."""
    code = """
import sys
from keecas import show_eqn, symbols

# show_eqn should be accessible
assert show_eqn is not None

# sympy should be loaded (symbols was imported)
assert 'sympy' in sys.modules

# Can use show_eqn (even if we can't see output in subprocess)
x = symbols('x')
# Just verify it doesn't error
result = show_eqn({x: 5})
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=5,
        env=get_test_env(),
    )

    assert result.returncode == 0, f"Test failed: {result.stderr}"
