import os

from doorstop.core import publisher, builder
from doorstop.cli import utilities


def on_pre_build(config):
    cwd = os.getcwd()
    path = os.path.abspath(os.path.join(cwd, "docs/gen"))
    tree = builder.build(cwd=cwd)

    published_path = publisher.publish(tree, path, ".md", index=True)

    if published_path:
        utilities.show("published: {}".format(published_path))
