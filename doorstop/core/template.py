# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to apply templates to documents."""

import os

from doorstop import common
from doorstop.core import Document
from doorstop.core.types import is_tree

CSS = os.path.join(os.path.dirname(__file__), "files", "doorstop.css")
HTMLTEMPLATE = "sidebar"
INDEX = "index.html"
MATRIX = "traceability.csv"

log = common.logger(__name__)


def get_template(obj, path, ext, template):
    """Return the correct template.

    Return correct template according to the published type.
    If a template has been specified, use that. Otherwise, use doorstop's
    built-in templates.

    Create the output folder and template folder.
    """

    # Set assets, ouput and template folders.
    if is_tree(obj):
        assets_dir = os.path.join(path, Document.ASSETS)  # path is a directory name
        template_dir = os.path.join(path, "template")
        output_dir = path
    else:
        assets_dir = os.path.join(
            os.path.dirname(path), Document.ASSETS
        )  # path is a filename
        template_dir = os.path.join(os.path.dirname(path), "template")
        output_dir = os.path.dirname(path)

    # Get the builtin templates.
    template_assets = os.path.join(os.path.dirname(__file__), "files", "templates")
    builtin_template = None
    # Check extension and set template folder accordingly.
    if ext == ".md":
        template_assets = template_assets + "/markdown"
    elif ext == ".tex":
        template_assets = template_assets + "/latex"
        builtin_template = "template/doorstop"
    elif ext == ".txt":
        template_assets = template_assets + "/text"
    else:
        template_assets = template_assets + "/html"
        builtin_template = HTMLTEMPLATE

    # Remove existing templates and assets first.
    if os.path.isdir(assets_dir):
        log.info("Deleting contents of assets directory %s", assets_dir)
        common.delete_contents(assets_dir)
    if os.path.isdir(template_dir):
        log.info("Deleting contents of template directory %s", template_dir)
        common.delete_contents(template_dir)

    # Only create template_dir if template actually exists.
    if os.path.isdir(template_assets):
        if not os.path.isdir(template_dir):
            os.makedirs(template_dir)

    # Create the output path only.
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    log.info(
        "Copying %s to %s",
        template_assets,
        os.path.join(os.path.dirname(path), "template"),
    )
    common.copy_dir_contents(template_assets, template_dir)

    # Return correct template and assets folder.
    if not template:
        return assets_dir, builtin_template

    return assets_dir, template
