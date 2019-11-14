# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd.documentation module command line utility
"""
import logging
import os
import sys

from .exceptions import DocBuildError, DocPublishError
from .plugin import build_documentation, publish_documentation
from ..utility import env_bool


logger_name = __name__
if logger_name == '__main__':
    logger_name = os.path.basename(__file__)
logger = logging.getLogger(logger_name)


def main():
    """
    screwdrivercd.documentation cli main entrypoint

    Returns
    -------
    int, optional:
        returncode - Returncode from the publication operation, 0=success
    """
    if env_bool('DOCUMENTATION_DEBUG', False):
        logging.basicConfig(level=logging.DEBUG)

    documentation_formats = os.environ.get('DOCUMENTATION_FORMATS', None)
    if documentation_formats:
        documentation_formats = [_.strip() for _ in documentation_formats.split(',')]

    if env_bool('DOCUMENTATION_PUBLISH', True):
        try:
            publish_documentation(documentation_formats=documentation_formats)
        except (DocBuildError, DocPublishError):
            sys.exit(1)
    else:
        try:
            build_documentation(documentation_formats=documentation_formats)
        except DocBuildError:
            sys.exit(1)
