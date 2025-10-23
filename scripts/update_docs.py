"""Update API documentation using quartodoc."""

import subprocess
import sys
from pathlib import Path


def update_api_docs():
    """Regenerate API reference from source code docstrings."""
    docs_dir = Path("docs")

    if not docs_dir.exists():
        print(f"ERROR: Documentation directory not found: {docs_dir}")
        sys.exit(1)

    # Run quartodoc to generate API reference
    print("Generating API documentation with quartodoc...")
    result = subprocess.run(
        ["uv", "run", "quartodoc", "build", "--config", str(docs_dir / "_quarto.yml")],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: API documentation generation failed:")
        print(result.stderr)
        sys.exit(1)

    if result.stdout:
        print(result.stdout)

    print("SUCCESS: API documentation generated successfully")

    # Validate output
    api_generated_dir = docs_dir / "api-reference"
    if not api_generated_dir.exists():
        print(f"WARNING: Generated API directory not created at {api_generated_dir}")
        sys.exit(1)

    # Count generated files
    generated_files = list(api_generated_dir.glob("*.qmd"))
    print(f"Generated {len(generated_files)} API reference pages:")
    for f in sorted(generated_files):
        print(f"   - {f.name}")

    # Check for sidebar
    sidebar_file = docs_dir / "api-reference" / "_sidebar.yml"
    if sidebar_file.exists():
        print(f"Sidebar configuration created: {sidebar_file}")
    else:
        print(f"WARNING: Sidebar file not found: {sidebar_file}")

    return 0


if __name__ == "__main__":
    sys.exit(update_api_docs())
