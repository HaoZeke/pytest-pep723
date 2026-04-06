=========
Changelog
=========

.. towncrier release notes start

pytest-pep723 0.1.0 (2026-04-06)
================================

Added
-----

- Built-in import-to-package mappings for 20+ packages where import name differs from PyPI name (PIL/pillow, sklearn/scikit-learn, etc.).
- CLI options: ``--pep723-check``, ``--pep723-paths``, ``--pep723-ignore`` for controlling scan scope.
- INI configuration: ``pep723_paths``, ``pep723_ignore_imports``, ``pep723_extra_mappings`` in pyproject.toml.
- Initial release of pytest-pep723. Statically verifies PEP 723 inline script metadata covers all imports.
- ``pep723`` pytest marker for selective test runs (``-m pep723`` or ``-m "not pep723"``).
