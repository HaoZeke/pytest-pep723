"""pytest-pep723: verify PEP 723 inline script metadata covers all imports."""

try:
    from pytest_pep723._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.0.dev0"
    __version_tuple__ = (0, 0, 0, "dev0")
