"""Tests for the bundled Claude Code skills and the `keecas skill` CLI."""

import ast
import os
import re
import subprocess
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "src" / "keecas" / "skills"
SKILL_NAMES = ("keecas-notebook", "keecas-quarto")

# Claude Code re-attaches only the first 5,000 tokens of an invoked skill after
# compaction. ~16k characters keeps SKILL.md safely below that.
MAX_SKILL_MD_CHARS = 16_000


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    assert match, "SKILL.md must start with YAML frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_frontmatter(name):
    """name matches the directory; description is present and within limits."""
    text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    fields = _frontmatter(text)
    assert fields["name"] == name
    description = fields["description"]
    assert 0 < len(description) <= 1024
    assert "<" not in description and ">" not in description


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_md_fits_compaction_budget(name):
    """SKILL.md stays small enough to survive compaction whole."""
    text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    assert len(text) <= MAX_SKILL_MD_CHARS


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_references_are_linked_and_have_contents(name):
    """Every reference file is linked from SKILL.md, and long ones open with a contents list."""
    skill_dir = SKILLS_DIR / name
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for reference in sorted((skill_dir / "references").glob("*.md")):
        assert f"references/{reference.name}" in skill_md
        lines = reference.read_text(encoding="utf-8").splitlines()
        if len(lines) > 100:
            assert "## Contents" in lines[:10], f"{reference.name} needs a contents list"


def test_skills_point_to_each_other():
    """Each skill names the other near the top, so the pointer survives compaction."""
    notebook_head = "\n".join(
        (SKILLS_DIR / "keecas-notebook" / "SKILL.md").read_text(encoding="utf-8").splitlines()[:15]
    )
    quarto_head = "\n".join(
        (SKILLS_DIR / "keecas-quarto" / "SKILL.md").read_text(encoding="utf-8").splitlines()[:15]
    )
    assert "keecas-quarto" in notebook_head
    assert "keecas-notebook" in quarto_head


def test_notebook_skeleton_runs_and_gives_correct_units():
    """The core skeleton's code cells execute and produce dimensionally correct values.

    The skeleton includes `h - c_nom - 5*u.mm`, a sum left as a factor of a
    product, which `pc.convert_to` must convert as a whole (keecas#118).
    """
    source = (SKILLS_DIR / "keecas-notebook" / "references" / "notebook_skeleton.md").read_text(
        encoding="utf-8"
    )
    blocks = re.findall(r"^```python\n(.*?)^```", source, flags=re.S | re.M)
    assert blocks

    namespace: dict = {}
    a_s_min_value = None
    for i, block in enumerate(blocks):
        exec(compile(ast.parse(block), f"skeleton-cell-{i}", "exec"), namespace)
        values = namespace.get("_v", {})
        if namespace.get("A_s_min") in values:
            a_s_min_value = values[namespace["A_s_min"]]

    # The value as computed by the skeleton's own pipeline line
    assert a_s_min_value is not None
    magnitude, unit = a_s_min_value.as_coeff_Mul()
    assert str(unit) == "millimeter**2"
    assert float(magnitude) == pytest.approx(311.2156, rel=1e-4)

    # The final verification passes (green, whatever the configured language)
    (check_result,) = namespace["_c"].values()
    assert r"\textcolor{green}" in check_result.data


def _cli_env(home: Path, **extra: str) -> dict[str, str]:
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    env.update(extra)
    return env


def test_skill_install_installs_all_skills(tmp_path):
    """`keecas skill install` installs both skills and is idempotent without --force."""
    for _ in range(2):
        result = subprocess.run(
            ["keecas", "skill", "install"],
            capture_output=True,
            text=True,
            env=_cli_env(tmp_path),
        )
        assert result.returncode == 0, result.stdout + result.stderr

    for name in SKILL_NAMES:
        assert (tmp_path / ".claude" / "skills" / name / "SKILL.md").exists()


def test_skill_print_survives_non_utf8_console(tmp_path):
    """`keecas skill print` emits UTF-8 even when the console encoding cannot encode the text."""
    result = subprocess.run(
        ["keecas", "skill", "print", "--quarto", "--with-references"],
        capture_output=True,
        env=_cli_env(tmp_path, PYTHONIOENCODING="ascii"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout.decode("utf-8")
    assert "# keecas calculation notebooks" in output
    assert "# keecas notebooks in Quarto projects" in output
    assert "## keecas-quarto/tables_and_plots.md" in output
    assert "name: keecas-notebook" not in output  # frontmatter stripped


def test_skill_print_defaults_to_core_skill(tmp_path):
    """Without --quarto only the keecas-notebook skill is printed."""
    result = subprocess.run(
        ["keecas", "skill", "print"],
        capture_output=True,
        env=_cli_env(tmp_path),
    )
    assert result.returncode == 0
    output = result.stdout.decode("utf-8")
    assert "# keecas calculation notebooks" in output
    assert "# keecas notebooks in Quarto projects" not in output
