# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Code style validation wrapper for screwdrivercd

This wrapper runs the pycodestyle validation tool.
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig
logging_basicConfig(check_prefix='STYLE_CHECK')

import logging
import os
import subprocess  # nosec
import sys

from pypirun.cli import interpreter_parent
from termcolor import colored

from ..utility import create_artifact_directory
from ..utility.environment import ins_filename
from ..utility.output import print_error
from ..utility.package import PackageMetadata, package_srcdir


logger_name = 'validate_style' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_with_codestyle(report_dir):
    """Run the codestyle command directly to do the validation"""

    package_metadata = PackageMetadata()
    package_name = package_metadata.metadata['name']
    src_dir = package_srcdir()

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
            if not os.path.exists(pycodestyle_command):
                pycodestyle_command = 'pycodestyle'

    # Generate the command line from the environment settings
    command = [pycodestyle_command]

    # Add extra arguments
    extra_args = os.environ.get('CODESTYLE_ARGS', '')
    if extra_args:
        command += extra_args.split()

    if src_dir and src_dir not in ['.']:
        target = src_dir
    else:
        # Add targets
        target = ''
        src_dir = '.'
        if hasattr(package_metadata, 'packages'):
            for package in package_metadata.packages:
                package_path = os.path.join(src_dir, package)
                if os.path.exists(package_path):
                    target = package_path
                    break

        if not target:
            if src_dir not in ['', '.'] and src_dir != package_name:
                target = os.path.join(src_dir, package_name.replace('.', '/'))
            else:
                target = package_name.replace('.', '/')

        print(f'target: {target}')
        target = ins_filename(target)
        if not target:
            print_error(f'ERROR: Unable to find package directory for package {package_name!r}, target directory {target!r} does not exist')
            return 1
    command.append(target)

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
        print(colored('OK: Code style validation successful', 'green'), flush=True)

    if rc > 0:
        print(colored('ERROR: Code style check failed', 'red'), file=sys.stderr, flush=True)
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
