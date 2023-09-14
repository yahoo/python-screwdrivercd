# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Type hint validation wrapper for screwdrivercd

This wrapper runs the validation tool.  This wrapper does the following:

- Runs the type checking tool with command line arguments to generate output in the formats specified by TYPE_CHECK_REPORT_FORMAT
- ensures all the logs and reports are stored in the build artifacts before exiting.
- Propagates a success code if the TYPE_CHECK_ENFORCING is set to false.
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='TEST_CHECK')

import logging
import os
import sys

from ..utility.output import header
from ..utility.tox import run_tox


logger_name = 'validate_test' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def main():
    tox_envlist = os.environ.get('TOX_ENVLIST', 'py38,py39,py310,py311')
    return run_tox(tox_envlist=tox_envlist)


if __name__ == '__main__':
    sys.exit(main())
