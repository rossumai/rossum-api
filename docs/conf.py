# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from __future__ import annotations

import os
import sys

import tomllib

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

with open("../pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

project = "Rossum API SDK"
copyright = "2025, Rossum"
author = "Rossum"
release = pyproject["project"]["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Suppress warning for included files
suppress_warnings = ["toc.not_included"]

# Napoleon settings for numpy-style docstrings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = False

# Autodoc settings
autodoc_default_options = {
    "members": "",
    "member-order": "bysource",
    "undoc-members": False,
}
autodoc_typehints_format = "short"

# Typehints configuration
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented_params"
typehints_fully_qualified = False
always_document_param_types = False
typehints_document_rtype = False
autodoc_class_signature = "mixed"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "_static/rossum-logo.svg"
html_favicon = "_static/rossum-logo.svg"
html_title = "Rossum API SDK"

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#1E6EE5",
        "color-brand-content": "#1E6EE5",
        "color-admonition-background": "rgba(30, 110, 229, 0.05)",
        "color-sidebar-background": "#ffffff",
        "color-sidebar-search-background": "#f5f7fa",
        "color-sidebar-search-border": "#e0e6ed",
        "color-sidebar-link-text--top-level": "#0d1117",
        "color-sidebar-item-background--hover": "rgba(30, 110, 229, 0.08)",
        "color-sidebar-item-expander-background--hover": "rgba(30, 110, 229, 0.08)",
        "font-stack": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font-stack--monospace": "'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace",
    },
    "dark_css_variables": {
        "color-brand-primary": "#61A0FF",
        "color-brand-content": "#61A0FF",
        "color-admonition-background": "rgba(97, 160, 255, 0.1)",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view"],
    "source_repository": "https://github.com/rossumai/rossum-api",
    "source_branch": "main",
    "source_directory": "docs/",
}


# Custom CSS and JS
def setup(app):
    app.add_css_file("custom.css")
    app.add_js_file("custom.js")
