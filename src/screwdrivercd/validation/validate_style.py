# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Code style validation wrapper for screwdrivercd

This wrapper runs the pycodestyle validation tool.
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='STYLE_CHECK')

import logging
import os
import subprocess  # nosec
import sys

from pypirun.cli import interpreter_parent
from termcolor import colored

from ..utility import create_artifact_directory
from ..utility.package import PackageMetadata


logger_name = 'validate_style' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_with_codestyle(report_dir):
    """Run the codestyle command directly to do the validation"""

    src_dir = os.environ.get('PACKAGE_DIR', '')
    if not src_dir:
        src_dir = os.environ.get('PACKAGE_DIRECTORY', '')

    parent_interpreter = interpreter_parent(sys.executable)
    interpreter = os.environ.get('BASE_PYTHON', parent_interpreter)
    bin_dir = os.path.dirname(interpreter)

    pycodestyle_command = os.path.join(bin_dir, 'pycodestyle')
    if not os.path.exists(pycodestyle_command):  # pragma: no cover
        bin_dir = os.path.dirname(sys.executable)
        pycodestyle_command = os.path.join(bin_dir, 'pycodestyle')
        if not os.path.exists(pycodestyle_command):
            bin_dir = os.path.dirname(parent_interpreter)
            pycodestyle_command = os.path.join(bin_dir, 'pycodestyle')

    package_name = PackageMetadata().metadata['name']

    # Generate the command line from the environment settings
    command = [pycodestyle_command]

    # Add extra arguments
    extra_args = os.environ.get('CODESTYLE_ARGS', '')
    if extra_args:
        command += extra_args.split()

    # Add targets
    if src_dir not in ['', '.'] and src_dir != package_name:
        command.append(os.path.join(src_dir, package_name.replace('.', '/')))
    else:
        command.append(package_name.replace('.', '/'))

    print('-' * 90 + '\nRunning:', ' '.join(command) + '\n' + '-' * 90, flush=True)
    rc = 0
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)  # nosec
    except subprocess.CalledProcessError as error:  # pragma: no cover
        rc = error.returncode
        output = error.output

    os.makedirs(report_dir, exist_ok=True)

    text_report = os.path.join(report_dir, 'codestyle.txt')

    with open(text_report, 'wb') as fh:
        for line in output.split(b'\n'):
            textline = line.decode(errors='ignore').strip()
            fh.write(line)
            if 'error:' in textline:  # pragma: no cover
                print(colored(textline, 'red'), flush=True)
            else:
                print(textline, flush=True)

    return rc


def validate_codestyle():
    """
    Run the codestyle validator tool and store the output

    Returns
    -------
    int:
        Exit returncode from the style validation command
    """
    logging_basicConfig()

    # Set the status message
    # update_job_status(status='SUCCESS', message='Checking code style')

    # Make sure the report directory exists
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    report_dir = os.path.join(artifacts_dir, 'reports/style_validation')
    create_artifact_directory(report_dir)

    rc = validate_with_codestyle(report_dir=report_dir)

    if rc == 0:
        print(colored('OK: Code style validation sucessful', 'green'), flush=True)
        update_job_status(status='SUCCESS', message='Code style check passed')

    if rc > 0:
        print(colored('ERROR: Type code style check failed', 'red'), file=sys.stderr, flush=True)
        update_job_status(status='FAILURE', message='Code style check failed')
        return rc

    return rc


def main() -> int:
    """
    Codestyle check runner utility command line entry point

    Returns
    -------
    int:
        Returncode from running the check
    """
    return validate_codestyle()


if __name__ == '__main__':
    sys.exit(main())
