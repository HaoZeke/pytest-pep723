import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "pytest-pep723"
copyright = "2026, Rohit Goswami"
author = "Rohit Goswami"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "sphinx_sitemap",
]

templates_path = ["_templates"]
exclude_patterns = []

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pytest": ("https://docs.pytest.org/en/stable", None),
}

# -- Options for HTML output -------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]

html_context = {
    "source_type": "github",
    "source_user": "HaoZeke",
    "source_repo": "pytest-pep723",
    "source_version": "main",
    "source_docs_path": "/docs/source/",
}

html_theme_options = {
    "github_url": "https://github.com/HaoZeke/pytest-pep723",
    "accent_color": "teal",
    "dark_code": True,
    "globaltoc_expand_depth": 1,
    "nav_links": [
        {
            "title": "PyPI",
            "url": "https://pypi.org/project/pytest-pep723/",
            "external": True,
        },
    ],
}

html_sidebars = {
    "**": [
        "sidebars/localtoc.html",
        "sidebars/repo-stats.html",
        "sidebars/edit-this-page.html",
    ],
}

autoapi_dirs = ["../../src/pytest_pep723"]
html_baseurl = "pytest-pep723.rgoswami.me"
