# pytest-pep723

A pytest plugin that verifies [PEP 723](https://peps.python.org/pep-0723/)
inline script metadata covers all imports.

When you use `uv run` to dispatch scripts with inline metadata blocks like:

```python
# /// script
# dependencies = [
#   "click",
#   "numpy",
# ]
# ///
```

...only the declared dependencies are available at runtime. If you add an
`import readcon` but forget to add `readcon` to the deps block, the script
fails at dispatch time. This plugin catches those gaps statically.

## Installation

```bash
uv add --group dev pytest-pep723
```

## Usage

```bash
# Scan all .py files under src/ for PEP 723 scripts
pytest --pep723-check --pep723-paths src/

# Ignore internal/conda-only packages
pytest --pep723-check --pep723-paths src/ --pep723-ignore mypkg --pep723-ignore ira_mod
```

Or configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pep723_paths =
    src/mypkg
pep723_ignore_imports =
    mypkg
    ira_mod
pep723_extra_mappings =
    gi=pygobject
    myspecial=my-special-pkg
```

Then just:

```bash
pytest --pep723-check
```

## What it checks

For every `.py` file under the configured paths that contains a
`# /// script` block:

1. Parses the declared dependencies from inline metadata
2. Extracts all `import` and `from X import` statements via AST
3. Skips stdlib and ignored imports
4. Maps import names to PyPI package names (handles `PIL` -> `pillow`, etc.)
5. Reports any import not covered by the declared deps

## Features

- Handles multi-line and single-line dependency formats
- Supports all version operators (`>=`, `~=`, `[extras]`, etc.)
- Built-in mapping for 20+ packages where import name differs from pip name
- Configurable ignore list for internal packages and conda-only deps
- Custom import-to-package mappings via `pep723_extra_mappings`
- Registers a `pep723` marker for selective test runs
