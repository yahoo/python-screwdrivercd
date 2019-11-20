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
logging_basicConfig(check_prefix='TYPE_CHECK')

import logging
import os
import subprocess  # nosec
import sys

from termcolor import colored
from ..utility import create_artifact_directory, env_bool
from ..utility.package import PackageMetadata


logger_name = 'validate_type' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_with_mypy(report_dir):
    """Run the mypy command directly to do the validation"""

    src_dir = os.environ.get('PACKAGE_DIR', '')
    if not src_dir:
        src_dir = os.environ.get('PACKAGE_DIRECTORY', '')

    package_name = PackageMetadata().metadata['name']

    # Generate the command line from the environment settings
    command = [sys.executable, '-m', 'mypy']

    # Add report arguments
    reports = os.environ.get('TYPE_CHECK_REPORT_FORMAT', 'txt').split(',')
    for report in [_.strip() for _ in reports]:
        if report in ['junit-xml']:
            command += ['--junit-xml', os.path.join(report_dir, 'mypy.xml')]
            continue
        command += [f'--{report}-report', report_dir]

    # Add extra arguments
    extra_args = os.environ.get('MYPY_ARGS', '')
    if extra_args:
        command += extra_args.split()

    # Add targets
    if src_dir not in ['', '.']:
        command += [src_dir]
    else:
        command += ['-p', package_name]

    print('-' * 90 + '\nRunning:', ' '.join(command) + '\n' + '-' * 90, flush=True)
    rc = 0
    try:
        output = subprocess.check_output(command)  # nosec
    except subprocess.CalledProcessError as error:
        rc = error.returncode
        output = error.output

    for line in output.decode(errors='ignore').split(os.linesep):
        line = line.strip()
        if 'error:' in line:
            print(colored(line, 'red'), flush=True)
        else:
            print(line, flush=True)

    text_report = os.path.join(report_dir, 'index.txt')
    if os.path.exists(text_report):
        with open(text_report) as fh:
            print(fh.read(), flush=True)

    return rc


def validate_type():
    """
    Run a type validator and store the output

    Returns
    -------
    int:
        Exit returncode from the type validation command or 0 if TYPE_CHECK_ENFORCING env variable is false
    """
    logging_basicConfig()

    # Set the status message
    # update_job_status(status='SUCCESS', message='Checking type annotations')

    # Make sure the report directory exists
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    report_dir = os.path.join(artifacts_dir, 'reports/type_validation')
    create_artifact_directory(report_dir)

    rc = validate_with_mypy(report_dir=report_dir)

    if rc > 0 and env_bool('TYPE_CHECK_ENFORCING'):
        print(colored('ERROR: Type check failed', 'red'), file=sys.stderr, flush=True)
        update_job_status(status='FAILURE', message='Type annotation check failed')
        return rc
    if rc == 0:
        print(colored('OK: Type validation sucessful', 'green'), flush=True)
        update_job_status(status='SUCCESS', message='Type annotation check passed')
    else:
        print(colored('WARNING: Type check failed, enforcement is disabled, so not failing check', 'yellow'))
        update_job_status(status='SUCCESS', message='Type annotation check, failed but is not enforcing')
        return 0
    return rc


def main():
    """
    Type check runner utility command line entry point

    Returns
    -------
    int:
        Returncode from running the check
    """
    return validate_type()


if __name__ == '__main__':
    main()
