# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to apply templates to documents."""

import os

from yaml import safe_load

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core import Document
from doorstop.core.types import is_tree

HTMLTEMPLATE = "doorstop"
INDEX = "index.html"
MATRIX = "traceability.csv"

REQUIRED_LATEX_PACKAGES = {
    "inputenc": None,
    "amsmath": None,
    "ulem": None,
    "longtable": None,
    "fancyvrb": None,
    "xr-hyper": None,
    "hyperref": ["unicode", "colorlinks"],
    "zref-user": None,
    "zref-xr": None,
}

log = common.logger(__name__)


def get_template(obj, path, ext, template):
    """Return the correct template.

    Return correct template according to the published type.
    If a template has been specified, use that. Otherwise, use doorstop's
    built-in templates.

    Create the output folder and template folder.
    """

    # Set assets, ouput and template folders.
    # If path ends with ext, use dirname since it is a file.
    if path.endswith(ext):
        path = os.path.dirname(path)
    # If html, add documents to path.
    if ext == ".html":
        assets_dir = os.path.join(path, "documents", Document.ASSETS)
    else:
        assets_dir = os.path.join(path, Document.ASSETS)
    template_dir = os.path.join(path, "template")
    output_dir = path

    if is_tree(obj):
        document_template = obj.documents[0].template
    else:
        document_template = obj.template

    # Check for custom template and verify that it is available.
    if template and not document_template:
        raise common.DoorstopError(
            "Template flag set, but no 'template' folder was found."
        )

    # Get the builtin templates.
    template_assets = os.path.join(os.path.dirname(__file__), "files", "templates")
    builtin_template = None
    # Check extension and set template folder accordingly.
    if ext == ".md":
        template_assets = os.sep.join([template_assets, "markdown"])
    elif ext == ".tex":
        template_assets = os.sep.join([template_assets, "latex"])
        builtin_template = "doorstop"
    elif ext == ".txt":
        template_assets = os.sep.join([template_assets, "text"])
    else:
        template_assets = os.sep.join([template_assets, "html"])
        builtin_template = HTMLTEMPLATE

    # Remove existing templates and assets first.
    if os.path.isdir(assets_dir):
        log.info("Deleting contents of assets directory %s", assets_dir)
        common.delete_contents(assets_dir)
    if os.path.isdir(template_dir):
        log.info("Deleting contents of template directory %s", template_dir)
        common.delete(template_dir)

    # Create the output path only.
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Copy template from document if it exists and template is given.
    if document_template and template:
        os.makedirs(template_dir)
        if is_tree(obj):
            for each in obj.documents:
                log.info(
                    "Copying %s to %s",
                    each.template,
                    os.path.join(os.path.dirname(path), "template"),
                )
                common.copy_dir_contents(each.template, template_dir)
        else:
            log.info(
                "Copying %s to %s",
                document_template,
                os.path.join(os.path.dirname(path), "template"),
            )
            common.copy_dir_contents(document_template, template_dir)

    # Only create template_dir if template actually exists.
    elif os.path.isdir(template_assets):
        os.makedirs(template_dir)
        log.info(
            "Copying %s to %s",
            template_assets,
            os.path.join(os.path.dirname(path), "template"),
        )
        common.copy_dir_contents(template_assets, template_dir)
        # If html template, also copy the default views files.
        if ext == ".html" and builtin_template:
            views_src_dir = os.path.join(os.path.dirname(__file__), "..", "views")
            views_tgt_dir = os.path.join(template_dir, "views")
            log.info("Copying %s to %s", views_src_dir, views_tgt_dir)
            os.makedirs(views_tgt_dir)
            common.copy_dir_contents(views_src_dir, views_tgt_dir)

    # Return correct template and assets folder.
    if not template:
        return assets_dir, builtin_template

    return assets_dir, template


def read_template_data(assets_dir, template):
    """Read the template data file and return the data."""
    try:
        template_data_file = os.path.abspath(
            os.path.join(assets_dir, "..", "template", "%s.yml" % template)
        )
        with open(template_data_file, "r") as f:
            template_data = safe_load(f)
    except Exception as ex:
        msg = "Template data load '{}' failed: {}".format(template_data_file, ex)
        raise DoorstopError(msg)
    return template_data


def check_latex_template_data(template_data, filename=None):
    """Check that all required packages have been defined in template data."""
    # Check basics first.
    if not isinstance(template_data, dict):
        log.error(
            "There seems to be a problem with the template configuration file '{}'.".format(
                filename
            )
        )
        raise DoorstopError(
            "There seems to be a problem with the template configuration file '{}'.".format(
                filename
            )
        )
    if "usepackage" not in template_data:
        log.error(
            "There is no dictionary of packages in the template configuration file '{}'.".format(
                filename
            )
        )
        raise DoorstopError(
            "There is no list of packages in the template configuration file '{}'.".format(
                filename
            )
        )
    if not isinstance(template_data["usepackage"], dict):
        log.error(
            "The 'usepackage' data in the configuration file is not a dictionary '{}'.".format(
                filename
            )
        )
        raise DoorstopError(
            "The 'usepackage' data in the configuration file is not a dictionary '{}'.".format(
                filename
            )
        )

    # Iterate over all required packages.
    for package, options in REQUIRED_LATEX_PACKAGES.items():
        if package not in template_data["usepackage"]:
            log.error(
                "%s is a required package. Please add it to the template configuration file.",
                package,
            )
            raise DoorstopError(
                "%s is a required package. Please add it to the template configuration file."
                % package,
            )
        if options:
            for option in options:
                if option not in template_data["usepackage"][package]:
                    log.error(
                        "%s is a required option for the %s package. Please add it to the template configuration file.",
                        option,
                        package,
                    )
                    raise DoorstopError(
                        "%s is a required option for the %s package. Please add it to the template configuration file."
                        % (option, package)
                    )
