"""Tests for the extraction/parsing logic."""

from pathlib import Path

from pytest_pep723.extract import (
    check_script,
    extract_imports,
    has_pep723_block,
    normalize_import_to_pkg,
    parse_pep723_deps,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestHasPEP723Block:
    def test_present(self):
        source = (FIXTURES / "good_script.py").read_text()
        assert has_pep723_block(source)

    def test_absent(self):
        source = (FIXTURES / "no_script_block.py").read_text()
        assert not has_pep723_block(source)


class TestParseDeps:
    def test_multiline_deps(self):
        source = (FIXTURES / "good_script.py").read_text()
        deps = parse_pep723_deps(source)
        assert deps == {"click", "numpy", "requests"}

    def test_singleline_deps(self):
        source = (FIXTURES / "singleline_deps.py").read_text()
        deps = parse_pep723_deps(source)
        assert deps == {"pandas", "numpy", "matplotlib"}

    def test_compat_release_operator(self):
        source = (FIXTURES / "compat_release_deps.py").read_text()
        deps = parse_pep723_deps(source)
        assert deps == {"ase", "click", "numpy"}

    def test_no_block(self):
        source = (FIXTURES / "no_script_block.py").read_text()
        assert parse_pep723_deps(source) == set()

    def test_version_specs_stripped(self):
        source = '# /// script\n# dependencies = [\n#   "foo>=1.2",\n#   "bar[extra]~=3.0",\n# ]\n# ///'
        deps = parse_pep723_deps(source)
        assert deps == {"foo", "bar"}


class TestExtractImports:
    def test_basic(self):
        source = (FIXTURES / "good_script.py").read_text()
        imports = extract_imports(source)
        assert "click" in imports
        assert "numpy" in imports
        assert "requests" in imports
        assert "sys" in imports

    def test_from_import(self):
        source = "from sklearn.linear_model import LinearRegression"
        imports = extract_imports(source)
        assert imports == {"sklearn"}

    def test_relative_import_ignored(self):
        source = "from . import foo"
        imports = extract_imports(source)
        assert imports == set()

    def test_syntax_error(self):
        assert extract_imports("def (broken") == set()


class TestNormalize:
    def test_known_mapping(self):
        assert normalize_import_to_pkg("PIL") == "pillow"
        assert normalize_import_to_pkg("sklearn") == "scikit-learn"

    def test_underscore_to_dash(self):
        assert normalize_import_to_pkg("my_package") == "my-package"

    def test_passthrough(self):
        assert normalize_import_to_pkg("requests") == "requests"


class TestCheckScript:
    def test_good_script(self):
        source = (FIXTURES / "good_script.py").read_text()
        assert check_script(source) == []

    def test_bad_script(self):
        source = (FIXTURES / "bad_script.py").read_text()
        missing = check_script(source)
        assert "numpy" in missing
        assert "requests" in missing

    def test_import_name_mismatch(self):
        source = (FIXTURES / "import_name_mismatch.py").read_text()
        assert check_script(source) == []

    def test_ignore_imports(self):
        source = (FIXTURES / "bad_script.py").read_text()
        missing = check_script(
            source, ignore_imports=frozenset(["numpy", "requests"])
        )
        assert missing == []

    def test_compat_release(self):
        source = (FIXTURES / "compat_release_deps.py").read_text()
        assert check_script(source) == []

    def test_singleline(self):
        source = (FIXTURES / "singleline_deps.py").read_text()
        assert check_script(source) == []
