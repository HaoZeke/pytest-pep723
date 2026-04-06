"""Pytest plugin for PEP 723 inline script dependency validation.

Automatically discovers Python files containing PEP 723 ``# /// script``
metadata blocks and verifies that every import is covered by the declared
inline dependencies.

Configuration (pyproject.toml)::

    [tool.pytest-pep723]
    paths = ["src/mypkg"]          # directories to scan (required)
    ignore_imports = ["mypkg"]     # imports to skip (internal packages, conda-only)
    extra_mappings = {"gi" = "pygobject"}  # additional import->pkg mappings

Or via CLI::

    pytest --pep723-check --pep723-paths src/mypkg
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_pep723.extract import (
    IMPORT_TO_PKG,
    check_script,
    find_pep723_scripts,
    has_pep723_block,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("pep723", "PEP 723 inline script validation")
    group.addoption(
        "--pep723-check",
        action="store_true",
        default=False,
        help="Enable PEP 723 inline script dependency checks.",
    )
    group.addoption(
        "--pep723-paths",
        action="append",
        default=[],
        help="Directories to scan for PEP 723 scripts (repeatable).",
    )
    group.addoption(
        "--pep723-ignore",
        action="append",
        default=[],
        help="Import names to ignore (repeatable). Internal packages, conda-only deps.",
    )
    parser.addini(
        "pep723_paths",
        type="linelist",
        help="Directories to scan for PEP 723 scripts.",
    )
    parser.addini(
        "pep723_ignore_imports",
        type="linelist",
        help="Import names to ignore (internal packages, conda-only deps).",
    )
    parser.addini(
        "pep723_extra_mappings",
        type="linelist",
        help="Extra import=package mappings, one per line (e.g. 'gi=pygobject').",
    )


def _get_config_paths(config: pytest.Config) -> list[Path]:
    """Resolve scan paths from CLI options or ini config."""
    cli_paths = config.getoption("pep723_paths", [])
    if cli_paths:
        return [Path(p).resolve() for p in cli_paths]
    ini_paths = config.getini("pep723_paths")
    if ini_paths:
        root = config.rootpath
        return [(root / p).resolve() for p in ini_paths]
    return []


def _get_ignore_imports(config: pytest.Config) -> frozenset[str]:
    """Resolve ignore set from CLI options or ini config."""
    cli_ignore: list[str] = config.getoption("pep723_ignore", [])
    ini_ignore: Sequence[str] = config.getini("pep723_ignore_imports")
    return frozenset([*cli_ignore, *ini_ignore])


def _apply_extra_mappings(config: pytest.Config) -> None:
    """Register extra import->package mappings from ini config."""
    mappings: Sequence[str] = config.getini("pep723_extra_mappings")
    for entry in mappings:
        if "=" in entry:
            imp, pkg = entry.split("=", 1)
            IMPORT_TO_PKG[imp.strip()] = pkg.strip()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "pep723: marks tests as PEP 723 inline script validation.",
    )
    _apply_extra_mappings(config)


class PEP723File(pytest.File):
    """Collector for a single PEP 723 script file."""

    def __init__(
        self,
        *,
        ignore_imports: frozenset[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._ignore_imports = ignore_imports

    def collect(self):
        yield PEP723Item.from_parent(
            self,
            name="pep723_deps",
            ignore_imports=self._ignore_imports,
        )


class PEP723Item(pytest.Item):
    """Test item that checks one PEP 723 script for uncovered imports."""

    def __init__(
        self,
        *,
        ignore_imports: frozenset[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._ignore_imports = ignore_imports
        self.add_marker("pep723")

    def runtest(self) -> None:
        source = self.path.read_text(encoding="utf-8")
        missing = check_script(source, ignore_imports=self._ignore_imports)
        if missing:
            raise PEP723DepError(self.path, missing)

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, PEP723DepError):
            return str(excinfo.value)
        return super().repr_failure(excinfo, style)

    def reportinfo(self):
        return self.path, None, f"pep723: {self.path.name}"


class PEP723DepError(Exception):
    """Raised when a PEP 723 script has uncovered imports."""

    def __init__(self, path: Path, missing: list[str]) -> None:
        self.path = path
        self.missing = missing

    def __str__(self) -> str:
        imports = ", ".join(self.missing)
        return (
            f"PEP 723 script {self.path.name} has imports not covered "
            f"by inline dependencies:\n"
            f"  Missing: {imports}\n"
            f"  File: {self.path}\n\n"
            f"Fix: add the missing package(s) to the # /// script "
            f"dependencies block."
        )


def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> PEP723File | None:
    config = parent.config
    if not config.getoption("pep723_check", False):
        return None
    if file_path.suffix != ".py":
        return None

    # Check if file is under any configured scan path
    scan_paths = _get_config_paths(config)
    if scan_paths:
        resolved = file_path.resolve()
        if not any(
            resolved == sp or sp in resolved.parents for sp in scan_paths
        ):
            return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not has_pep723_block(content):
        return None

    ignore_imports = _get_ignore_imports(config)
    return PEP723File.from_parent(
        parent,
        path=file_path,
        ignore_imports=ignore_imports,
    )
