# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd.documentation module command line utility
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='DOCUMENTATION')
import logging
import os
import sys

from .exceptions import DocBuildError, DocPublishError
from .plugin import build_documentation, publish_documentation
from ..utility import env_bool


logger_name = __name__
if logger_name == '__main__':  # pragma: no cover
    logger_name = os.path.basename(__file__)
logger = logging.getLogger(logger_name)


def main():  # pragma: no cover
    """
    screwdrivercd.documentation cli main entrypoint

    Returns
    -------
    int, optional:
        returncode - Returncode from the publication operation, 0=success
    """
    documentation_formats = os.environ.get('DOCUMENTATION_FORMATS', 'mkdocs,sphinx')

    if documentation_formats:
        documentation_formats = [_.strip() for _ in documentation_formats.split(',')]

    if env_bool('DOCUMENTATION_PUBLISH', True):  # pragma: no cover
        try:
            publish_documentation(documentation_formats=documentation_formats)
        except (DocBuildError, DocPublishError):
            return 1
    else:
        try:
            build_documentation(documentation_formats=documentation_formats)
        except DocBuildError:
            return 1
    update_job_status(status='SUCCESS', message=f'Generated {", ".join(documentation_formats)} documentation')
