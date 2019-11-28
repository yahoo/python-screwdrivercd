# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Code style validation wrapper for screwdrivercd

This wrapper runs the pycodestyle validation tool.
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='PACKAGE_QUALITY_CHECK')

import logging
import os
import subprocess  # nosec
import sys
from termcolor import colored

from typing import List

from ..utility.environment import env_int, env_bool, interpreter_bin_command
from ..utility.run import run_and_log_output

logger_name = 'validate_package_quality' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_package_quality(package_dir: str='') -> int:
    """
    Run the pyroma tool to validate the quality of packages in the package directory

    Parameters
    ----------
    package_dir: str
        The package directory containing the packages to check

    Returns
    -------
    int:
        Return code from the validation command
    """
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    report_dir = os.path.join(artifacts_dir, 'reports/package_quality_validation')
    package_dir = os.path.join(artifacts_dir, 'packages')
    pyroma_min_score = env_int('PYROMA_MIN_SCORE', 8)
    fail_if_no_packages = env_bool('VALIDATE_PACKAGE_QUALITY_FAIL_MISSING', True)

    if not os.path.exists(package_dir):
        print(f'Package directory {package_dir!r} is not present, no packages to validate')
        if fail_if_no_packages:
            return 1
        else:
            return 0
    return_codes: List[int] = []
    for package in os.listdir(package_dir):
        if package.endswith('.whl'):
            continue
        print(f'Checking package: {package}', flush=True, end='')
        package_filename = os.path.join(package_dir, package)
        report_filename = f'{report_dir}/{package}.log'
        command = [interpreter_bin_command('pyroma'), f'--min={pyroma_min_score}', package_filename]
        try:
            run_and_log_output(command, logfile=report_filename)
            return_codes.append(0)
        except subprocess.CalledProcessError as error:
            print(f' ... {colored("Failed", "red")}', flush=True)
            return_codes.append(error.returncode)
    return sum(return_codes)


def main() -> int:
    """
    Pyroma utility running command line utility entry point

    Returns
    -------
    int:
        Returncode from running the check
    """
    return validate_package_quality()  # pragma: no cover


if __name__ == '__main__':
    sys.exit(main())
