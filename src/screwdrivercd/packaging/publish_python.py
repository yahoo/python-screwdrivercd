# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Python packaging publish command line wrapper
"""
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='PUBLISH_PYTHON')

import os
import subprocess  # nosec
import sys

from ..utility.environment import env_bool, interpreter_bin_command, standard_directories


def main(twine_command: str='') -> int:
    if not twine_command:
        twine_command = interpreter_bin_command('twine')

    directories = standard_directories(command='publish_python')
    user = os.environ.get('PYPI_USER', None)
    password = os.environ.get('PYPI_PASSWORD', None)
    twine_repository_url = os.environ.get('TWINE_REPOSITORY_URL', 'https://upload.pypi.org/legacy/')

    if not os.path.exists(directories['packages']):
        print(f'Package directory {directories["packages"]!r} does not exist, no packages to publish', flush=True)
        return 0

    if not env_bool('PUBLISH_PYTHON', True):
        print('Publish is disabled, skipping publish operation', flush=True)
        return 0

    bad_cred_rc = 0
    if env_bool('PUBLISH_PYTHON_FAIL_MISSING_CRED', False):
        bad_cred_rc = 1

    if 'test.pypi.org' in twine_repository_url:
        print('Using test.pypi.org endpoint, getting user from TEST_PYPI_USER secret and password from TEST_PYPI_PASSWORD secret', flush=True)
        user = os.environ.get('TEST_PYPI_USER', None)
        password = os.environ.get('TEST_PYPI_PASSWORD', None)

    if not user:
        print('Unable to publish to PYPI, user secret is not set', flush=True)
        return bad_cred_rc

    if not password:
        print('Unable to publish to PYPI, password secret is not set', flush=True)
        return bad_cred_rc

    if not os.path.exists(twine_command):
        print('The twine command is missing', flush=True)
        return 1

    print(f'Publishing to {twine_repository_url} as user {user}', flush=True)

    failed = []
    for filename in os.listdir(directories['packages']):
        print(f'Uploading {filename}', flush=True)
        command = [twine_command, 'upload', '--verbose', os.path.join(directories['packages'], filename)]

        print(f'Running: {" ".join(command)}')
        twine_env = {'TWINE_USERNAME': user, 'TWINE_PASSWORD': password, 'TWINE_REPOSITORY_URL': twine_repository_url}

        log_filename = os.path.join(directories['logs'], f'twine_{filename}.log')
        with open(log_filename, 'ab') as output_handle:
            try:
                subprocess.check_call(command, env=twine_env, stdout=output_handle, stderr=subprocess.STDOUT)  # nosec
            except subprocess.CalledProcessError as error:
                print(f'Upload of package file {filename!r} failed, returncode {error.returncode}', flush=True)
                output_handle.write(f'Upload of package file {filename!r} failed, returncode {error.returncode}'.encode(errors='ignore'))
                failed.append(filename)
                if error.stdout:
                    output_handle.write(error.stdout)
                if error.stderr:
                    output_handle.write(error.stderr)

    if failed:
        update_job_status(status='FAILURE', message=f'{len(failed)} packages failed')
        return len(failed)

    return 0
