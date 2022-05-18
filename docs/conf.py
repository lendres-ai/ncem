#!/usr/bin/env python
# mypy: ignore-errors
# ncem documentation build configuration file
#
# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(".."))


# -- General configuration ---------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.7'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.

# Add 'sphinx_automodapi.automodapi' if you want to build modules
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
]

# Generate the API documentation when building
autosummary_generate = True
autodoc_member_order = "bysource"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = True
napoleon_use_param = True
napoleon_custom_sections = [("Params", "Parameters")]

intersphinx_mapping = dict(
    anndata=("https://anndata.readthedocs.io/en/latest/", None),
    scanpy=("https://scanpy.readthedocs.io/en/latest/", None),
    numpy=("https://docs.scipy.org/doc/numpy/", None),
    pandas=("http://pandas.pydata.org/pandas-docs/stable/", None),
    python=("https://docs.python.org/3", None),
    scipy=("https://docs.scipy.org/doc/scipy/reference/", None),
)

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "ncem"
copyright = "2021, theislab"
author = "David S. Fischer, Anna C. Schaar"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = "0.1.3"
# The full version, including alpha/beta/rc tags.
release = "0.1.3"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a
# theme further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = dict(
    navigation_depth=4,
)
html_context = dict(
    display_github=True,  # Integrate GitHub
    github_user="theislab",  # Username
    github_repo="ncem",  # Repo name
    github_version="main",  # Version
    conf_py_path="/docs/",  # Path in the checkout to the docs root
)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_show_sphinx = False
gh_url = "https://github.com/{github_user}/{github_repo}".format_map(html_context)


def setup(app):
    app.add_css_file('css/custom.css')
    app.connect('autodoc-process-docstring', insert_function_images)
    app.add_role('pr', autolink(f'{gh_url}/pull/{{}}', 'PR {}'))

# -- Options for HTMLHelp output ---------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "ncemdoc"


# -- Options for LaTeX output ------------------------------------------

latex_elements = {
    # The paper size ("letterpaper" or "a4paper").
    #
    # "papersize": "letterpaper",
    # The font size ("10pt", "11pt" or "12pt").
    #
    # "pointsize": "10pt",
    # Additional stuff for the LaTeX preamble.
    #
    # "preamble": "",
    # Latex figure (float) alignment
    #
    # "figure_align": "htbp",
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "ncem.tex",
        "ncem Documentation",
        "Anna Schaar",
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        "ncem",
        "ncem Documentation",
        [author],
        1,
    )
]

autodoc_typehints = "description"


# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "ncem",
        "ncem Documentation",
        author,
        "ncem",
        "One line description of project.",
        "Miscellaneous",
    ),
]

html_css_files = [
    "custom_cookietemple.css",
]

# -- Images for plot functions -------------------------------------------------


def insert_function_images(app, what, name, obj, options, lines):
    path = Path(__file__).parent / 'api' / f'{name}.png'
    if what != 'function' or not path.is_file(): return
    lines[0:0] = [f'.. image:: {path.name}', '   :width: 200', '   :align: right', '']

# -- GitHub links --------------------------------------------------------------


def autolink(url_template, title_template='{}'):
    from docutils import nodes

    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        url = url_template.format(text)
        title = title_template.format(text)
        node = nodes.reference(rawtext, title, refuri=url, **options)
        return [node], []
    return role
