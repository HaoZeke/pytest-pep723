"""Parse PEP 723 inline script metadata and extract imports from Python files."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# Well-known top-level import -> PyPI package mapping for packages where
# the import name differs from the pip name.
IMPORT_TO_PKG: dict[str, str] = {
    "PIL": "pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "attr": "attrs",
    "Bio": "biopython",
    "gi": "pygobject",
    "Crypto": "pycryptodome",
    "serial": "pyserial",
    "usb": "pyusb",
    "wx": "wxpython",
    "pkg_resources": "setuptools",
    "dateutil": "python-dateutil",
    "google": "google-api-python-client",
    "IPython": "ipython",
    "skimage": "scikit-image",
    "mpl_toolkits": "matplotlib",
    "adjustText": "adjusttext",
    "resvg": "resvg-py",
}

# Standard library modules -- use sys.stdlib_module_names on 3.10+.
STDLIB: frozenset[str] = frozenset(
    getattr(sys, "stdlib_module_names", set())
    | {
        # Fallback for older Pythons missing stdlib_module_names
        "sys",
        "os",
        "pathlib",
        "logging",
        "re",
        "json",
        "math",
        "functools",
        "itertools",
        "collections",
        "typing",
        "dataclasses",
        "abc",
        "io",
        "warnings",
        "contextlib",
        "copy",
        "enum",
        "textwrap",
        "shutil",
        "subprocess",
        "tempfile",
        "argparse",
        "unittest",
        "hashlib",
        "struct",
        "operator",
        "importlib",
        "inspect",
        "string",
        "glob",
        "fnmatch",
        "time",
        "datetime",
        "calendar",
        "random",
        "statistics",
        "decimal",
        "fractions",
        "numbers",
        "array",
        "queue",
        "threading",
        "multiprocessing",
        "concurrent",
        "socket",
        "http",
        "urllib",
        "email",
        "html",
        "xml",
        "csv",
        "configparser",
        "pprint",
        "traceback",
        "pickle",
        "shelve",
        "sqlite3",
        "gzip",
        "zipfile",
        "tarfile",
        "lzma",
        "bz2",
        "site",
        "sysconfig",
        "platform",
        "signal",
        "ctypes",
        "weakref",
        "types",
        "gc",
        "dis",
        "ast",
        "token",
        "tokenize",
        "pdb",
        "profile",
        "cProfile",
        "timeit",
        "resource",
        "errno",
        "select",
        "selectors",
        "mmap",
        "codecs",
        "locale",
        "gettext",
        "unicodedata",
        "stringprep",
        "readline",
        "rlcompleter",
        "difflib",
        "pydoc",
        "doctest",
        "secrets",
        "uuid",
        "base64",
        "binascii",
        "hmac",
        "ssl",
        "ftplib",
        "poplib",
        "imaplib",
        "smtplib",
        "xmlrpc",
        "asyncio",
        "__future__",
        "tomllib",
    }
)


def has_pep723_block(source: str) -> bool:
    """Check whether source contains a PEP 723 script metadata block."""
    return "# /// script" in source


def parse_pep723_deps(source: str) -> set[str]:
    """Extract normalized package names from a PEP 723 script block.

    Returns the set of lowercased package names (version specs stripped).
    """
    match = re.search(
        r"^# /// script\s*\n((?:#[^\n]*\n)*?)# ///",
        source,
        re.MULTILINE,
    )
    if not match:
        return set()
    block = match.group(1)
    # Strip comment prefixes and join
    stripped = "\n".join(line.lstrip("#").strip() for line in block.splitlines())
    dep_match = re.search(r"dependencies\s*=\s*\[(.*)\]", stripped, re.DOTALL)
    if not dep_match:
        return set()
    deps_block = dep_match.group(1)
    deps: set[str] = set()
    for m in re.finditer(r'"([^"]+)"', deps_block):
        raw = m.group(1)
        pkg = re.split(r"[>=<!\[;~]", raw)[0].strip().lower()
        deps.add(pkg)
    return deps


def extract_imports(source: str) -> set[str]:
    """Extract all top-level package names from import statements in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
    return modules


def normalize_import_to_pkg(imp: str) -> str:
    """Map an import name to the expected PyPI package name."""
    if imp in IMPORT_TO_PKG:
        return IMPORT_TO_PKG[imp].lower()
    return imp.lower().replace("_", "-")


def check_script(
    source: str,
    ignore_imports: frozenset[str] = frozenset(),
) -> list[str]:
    """Check a PEP 723 script for uncovered imports.

    Returns a list of import names that are not covered by the declared
    inline dependencies, stdlib, or the ignore set.
    """
    declared = parse_pep723_deps(source)
    imports = extract_imports(source)
    missing: list[str] = []
    for imp in sorted(imports):
        if imp in STDLIB:
            continue
        if imp in ignore_imports:
            continue
        expected_pkg = normalize_import_to_pkg(imp)
        if expected_pkg not in declared and imp.lower() not in declared:
            missing.append(imp)
    return missing


def find_pep723_scripts(root: Path) -> list[Path]:
    """Recursively find .py files under root with PEP 723 script blocks."""
    scripts: list[Path] = []
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if has_pep723_block(content):
            scripts.append(py_file)
    return scripts
