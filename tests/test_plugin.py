"""Integration tests for the pytest plugin using pytester."""

import textwrap

import pytest


@pytest.fixture
def good_script_content():
    return textwrap.dedent("""\
        # /// script
        # dependencies = [
        #   "click",
        #   "numpy",
        # ]
        # ///
        import sys
        import click
        import numpy as np
        print("hello")
    """)


@pytest.fixture
def bad_script_content():
    return textwrap.dedent("""\
        # /// script
        # dependencies = [
        #   "click",
        # ]
        # ///
        import sys
        import click
        import numpy as np
        import requests
        print("hello")
    """)


class TestPluginCollection:
    def test_no_collection_without_flag(self, pytester, good_script_content):
        """Without --pep723-check, no PEP 723 items are collected."""
        pytester.makefile(".py", myscript=good_script_content)
        result = pytester.runpytest("--collect-only")
        result.stdout.fnmatch_lines(["*no tests ran*"])

    def test_collects_with_flag(self, pytester, good_script_content):
        """With --pep723-check, PEP 723 scripts are collected."""
        pytester.makefile(".py", myscript=good_script_content)
        result = pytester.runpytest("--pep723-check", "--collect-only")
        result.stdout.fnmatch_lines(["*pep723_deps*"])

    def test_skips_non_pep723_files(self, pytester):
        """Files without PEP 723 blocks are not collected."""
        pytester.makefile(
            ".py",
            regular="import sys\nprint('hello')\n",
        )
        result = pytester.runpytest("--pep723-check", "--collect-only")
        result.stdout.fnmatch_lines(["*no tests ran*"])


class TestPluginResults:
    def test_good_script_passes(self, pytester, good_script_content):
        pytester.makefile(".py", myscript=good_script_content)
        result = pytester.runpytest("--pep723-check", "-v")
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0

    def test_bad_script_fails(self, pytester, bad_script_content):
        pytester.makefile(".py", myscript=bad_script_content)
        result = pytester.runpytest("--pep723-check", "-v")
        result.stdout.fnmatch_lines(["*FAILED*"])
        result.stdout.fnmatch_lines(["*numpy*"])
        result.stdout.fnmatch_lines(["*requests*"])
        assert result.ret != 0

    def test_bad_script_with_ignore(self, pytester, bad_script_content):
        """Ignored imports should not cause failures."""
        pytester.makefile(".py", myscript=bad_script_content)
        result = pytester.runpytest(
            "--pep723-check",
            "--pep723-ignore=numpy",
            "--pep723-ignore=requests",
            "-v",
        )
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0


class TestPluginPaths:
    def test_path_filter(self, pytester, good_script_content, bad_script_content):
        """Only scripts under --pep723-paths are checked."""
        sub = pytester.mkdir("subdir")
        (sub / "good.py").write_text(good_script_content)
        # Bad script is outside the scanned path
        pytester.makefile(".py", bad=bad_script_content)
        result = pytester.runpytest(
            "--pep723-check",
            f"--pep723-paths={sub}",
            "-v",
        )
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0


class TestIniConfig:
    def test_ini_paths(self, pytester, good_script_content):
        """pep723_paths ini option works."""
        sub = pytester.mkdir("scripts")
        (sub / "myscript.py").write_text(good_script_content)
        pytester.makeini(
            textwrap.dedent("""\
            [pytest]
            pep723_paths =
                scripts
            """)
        )
        result = pytester.runpytest("--pep723-check", "-v")
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0

    def test_ini_ignore(self, pytester, bad_script_content):
        """pep723_ignore_imports ini option works."""
        pytester.makefile(".py", myscript=bad_script_content)
        pytester.makeini(
            textwrap.dedent("""\
            [pytest]
            pep723_ignore_imports =
                numpy
                requests
            """)
        )
        result = pytester.runpytest("--pep723-check", "-v")
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0

    def test_ini_extra_mappings(self, pytester):
        """pep723_extra_mappings ini option works."""
        pytester.makefile(
            ".py",
            myscript=textwrap.dedent("""\
                # /// script
                # dependencies = [
                #   "my-special-pkg",
                # ]
                # ///
                import myspecial
                print("hello")
            """),
        )
        pytester.makeini(
            textwrap.dedent("""\
            [pytest]
            pep723_extra_mappings =
                myspecial=my-special-pkg
            """)
        )
        result = pytester.runpytest("--pep723-check", "-v")
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0


class TestMarker:
    def test_pep723_marker_registered(self, pytester, good_script_content):
        """The pep723 marker is registered and selectable."""
        pytester.makefile(".py", myscript=good_script_content)
        result = pytester.runpytest("--pep723-check", "-m", "pep723", "-v")
        result.stdout.fnmatch_lines(["*PASSED*"])
        assert result.ret == 0
