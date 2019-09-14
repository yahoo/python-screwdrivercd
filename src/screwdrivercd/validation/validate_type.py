# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Type hint validation wrapper for screwdrivercd
"""
import logging
import os
import subprocess  # nosec
import sys
from ..utility import colored, create_artifact_directory, run_exit_on_error


logger_name = 'validate_type' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_with_mypy(report_dir):
    """Run the mypy command directly to do the validation"""

    package_name = subprocess.check_output([sys.executable, 'setup.py', '--name']).decode(errors='ignore').strip().split(os.linesep)[-1]  # nosec

    # Generate the command line from the environment settings
    command = ['pypirun', 'lxml,mypy', 'mypy']

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
    # Make sure the report directory exists
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    report_dir = os.path.join(artifacts_dir, 'reports/type_validation')
    create_artifact_directory(report_dir)

    rc = validate_with_mypy(report_dir=report_dir)

    if rc > 0 and os.environ.get('TYPE_CHECK_ENFORCING', 'false').lower() in ['true', '1', 'on']:
        print(colored('ERROR: Type check failed', 'red'), file=sys.stderr, flush=True)
        sys.exit(rc)
    if rc == 0:
        print(colored('OK: Type validation sucessful', 'green'), flush=True)
    else:
        print(colored('WARNING: Type check failed, enforcement is disabled, so not failing check', 'yellow'))
    sys.exit(0)


def main():
    return validate_type()
