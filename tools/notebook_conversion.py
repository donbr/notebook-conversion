"""Notebook conversion utility.

Converts every .ipynb in the repo into paired .py and .md files using Jupytext
and maintains a top-level interim/index.md catalog.

Usage:
    python tools/notebook_conversion.py --all        # convert/refresh all notebooks
    python tools/notebook_conversion.py --check      # exit 1 if any pair is stale
"""
from __future__ import annotations

import sys
import subprocess
import json
import os
from pathlib import Path
from typing import Iterable, List

import click
import jupytext
import nbformat as _nbf

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_MD_PATH = REPO_ROOT / "interim" / "index.md"
RAW_DIR = REPO_ROOT / "raw"

# Characters allowed in a sanitized filename
_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")

# Words to drop from generated slugs / titles – not meaningful to notebook purpose
_STOPWORDS = {
    "ai",
    "makerspace",
    "ai_makerspace",
    "assignment",
    "assignments",
    "task",
    "2025",
    "2024",
}

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def find_notebooks() -> Iterable[Path]:
    """Yield all *.ipynb files inside the raw directory."""
    if not RAW_DIR.exists():
        return []
    return RAW_DIR.rglob("*.ipynb")


def _sanitize(stem: str) -> str:
    """Return a lowercase, filename-safe slug (letters, digits, dash, underscore)."""
    # Remove parentheses and convert word separators to dash
    stem = (
        stem.lower()
        .replace("(", " ")
        .replace(")", " ")
        .replace("_", " ")
        .replace("-", " ")
    )
    # Filter out stopwords
    tokens = [t for t in stem.split() if t and t not in _STOPWORDS]
    if not tokens:
        tokens = ["notebook"]
    stem = "-".join(tokens)
    slug = "".join(c.lower() if c.lower() in _ALLOWED_CHARS else "-" for c in stem)
    # collapse consecutive dashes
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "notebook"


def paired_paths(dest_nb_path: Path) -> tuple[Path, Path]:
    """Return paths for the pure-code and pure-markdown exports.

    We append explicit suffixes so it's obvious which file holds what:
    -   `<slug>-py-only.py`
    -   `<slug>-md-only.md`
    """
    stem = dest_nb_path.stem
    folder = dest_nb_path.with_suffix("").parent
    py_path = folder / f"{stem}-py-only.py"
    md_path = folder / f"{stem}-md-only.md"
    return py_path, md_path


def process_notebook(raw_nb: Path) -> tuple[Path, bool]:
    """Copy *raw_nb* into interim/, sanitize name, then create py/md.

    Returns (dest_nb_path, changed) where *changed* is True if any file was created/updated."""

    sanitized = _sanitize(raw_nb.stem)
    dest_folder = INDEX_MD_PATH.parent / sanitized
    dest_folder.mkdir(parents=True, exist_ok=True)
    dest_nb = dest_folder / f"{sanitized}.ipynb"

    changed = False
    # Copy notebook if new or different
    raw_bytes = raw_nb.read_bytes()
    if not dest_nb.exists() or dest_nb.read_bytes() != raw_bytes:
        dest_nb.write_bytes(raw_bytes)
        changed = True

    # Now convert dest notebook
    py_path, md_path = paired_paths(dest_nb)

    # Read the notebook once
    nb = jupytext.read(dest_nb)

    # ----------------------------------------------------------------------------------
    # Split cells: code → for the .py file, markdown → for the .md file
    # ----------------------------------------------------------------------------------
    code_nb = _nbf.v4.new_notebook(metadata=nb.metadata)
    code_nb.cells = [c for c in nb.cells if c.get("cell_type") == "code"]

    md_nb = _nbf.v4.new_notebook(metadata=nb.metadata)
    md_nb.cells = [c for c in nb.cells if c.get("cell_type") == "markdown"]

    # --- Write python file (percent format, CODE CELLS ONLY) ---
    new_py_content = jupytext.writes(code_nb, fmt="py:percent")
    if not py_path.exists() or py_path.read_text(encoding="utf-8", errors="ignore") != new_py_content:
        header = (
            f"# Generated from {dest_nb.relative_to(REPO_ROOT)}.\n"
            "# Do not edit directly; edit the notebook instead and re-run conversion.\n\n"
        )
        py_path.write_text(header + new_py_content, encoding="utf-8")
        changed = True

    # --- Write markdown file (MARKDOWN CELLS ONLY) ---
    new_md_content = jupytext.writes(md_nb, fmt="md")
    link_to_py = py_path.relative_to(md_path.parent)
    header = f"[View paired Python script]({link_to_py})\n\n"
    if not md_path.exists() or md_path.read_text(encoding="utf-8", errors="ignore") != header + new_md_content:
        md_path.write_text(header + new_md_content, encoding="utf-8")
        changed = True

    return dest_nb, changed


def build_index(nb_paths: List[Path]):
    """Generate notebooks/index.md linking every pair."""
    if not nb_paths:
        return
    INDEX_MD_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Notebook Catalogue\n", "\n"]
    index_dir = INDEX_MD_PATH.parent
    for nb in sorted(nb_paths, key=lambda p: p.stem.lower()):
        py_path, md_path = paired_paths(nb)
        if not py_path.exists() or not md_path.exists():
            continue

        # Compute paths relative to the index file directory in a way that never raises
        rel_py = Path(os.path.relpath(py_path, index_dir)).as_posix()
        rel_md = Path(os.path.relpath(md_path, index_dir)).as_posix()

        display_name = " ".join(token.capitalize() for token in nb.stem.split("-") if token)
        lines.append(f"- **{display_name}** - [Code]({rel_py}) / [Docs]({rel_md})\n")

    INDEX_MD_PATH.write_text("".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

@click.command()
@click.option("--all", "convert_all", is_flag=True, help="Convert all notebooks (default if no flag).")
@click.option("--check", is_flag=True, help="Only check if conversion is up-to-date; exits 1 if stale.")
def cli(convert_all: bool = False, check: bool = False):
    """Notebook conversion CLI."""
    if not (convert_all or check):
        convert_all = True  # default behaviour

    dest_notebooks: List[Path] = []
    raw_notebooks: List[Path] = list(find_notebooks())

    for raw_nb in raw_notebooks:
        dest_nb, changed = process_notebook(raw_nb)
        dest_notebooks.append(dest_nb)

    # Regenerate index when anything changed or --all requested
    build_index(dest_notebooks)

    if check and dest_notebooks:
        click.echo("The following notebooks have outdated pairs:", err=True)
        for nb in dest_notebooks:
            click.echo(f"  - {nb.relative_to(REPO_ROOT)}", err=True)
        sys.exit(1)

    click.echo("Notebook conversion complete." if not check else "All notebooks are up-to-date.")


if __name__ == "__main__":
    cli()  # type: ignore[call-arg] 