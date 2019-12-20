# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Python packaging publish command line wrapper
"""
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='PUBLISH_PYTHON')

import logging
import os
import subprocess  # nosec
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import requests
from pkg_resources import safe_name

from ..utility.environment import env_bool, interpreter_bin_command, standard_directories
from ..utility.package import setup_query


logger = logging.getLogger(__name__)


def package_exists(package: str, package_filename: str, endpoint: str='https://pypi.org/simple') -> bool:
    url = f'{endpoint}/{safe_name(package)}/'

    # Stream the index
    req = requests.get(url, stream=True)
    for line in req.iter_lines():
        line = line.decode(errors='ignore')
        if package_filename in line:
            return True
    return False


def poll_until_available(package: str, packages: Set[str], endpoint: str='https://pypi.org/simple', timeout=300, poll_interval=15) -> Set[str]:
    """
    Poll the packaging repository until package files show up in the index

    Parameters
    ----------
    package: str
        The package the package files are published for

    packages: set of str
        Packages to poll for

    endpoint: str, optional
        The packaging repository endpoint to poll, default=https://pypi.org/simple

    timeout: int, optional
        Timeout in seconds, default=300

    poll_interval: int, optional
        Frequency to poll the package repository

    Returns
    ------
    set:
        Set of packages that failed to publish, empty set if no packages failed
    """
    start = datetime.utcnow()
    end = start + timedelta(seconds=timeout)
    completed: Set[str] = set()

    delay = 1
    while datetime.utcnow() < end:
        for filename in packages - completed:
            if package_exists(package, filename, endpoint=endpoint):
                completed.add(filename)

        elapsed = datetime.utcnow() - start
        not_published = packages - completed
        print(f'\t{elapsed}: Published: {list(completed)}, Waiting for: {list(not_published)}', flush=True)
        
        if completed == packages:
            return set()

        if delay < poll_interval:
            delay = delay * 2
        if delay > poll_interval:  # pragma: no cover
            delay = poll_interval
        time.sleep(delay)
    return packages - completed


def main(twine_command: str='') -> int:
    if not twine_command:  # pragma: no cover
        twine_command = interpreter_bin_command('twine')

    directories = standard_directories(command='publish_python')
    user = os.environ.get('PYPI_USER', None)
    password = os.environ.get('PYPI_PASSWORD', None)
    publish_timeout = int(os.environ.get('PUBLISH_PYTHON_TIMEOUT', os.environ.get('ARTIFACTORY_TIMEOUT', "300")))

    twine_repository_url = os.environ.get('TWINE_REPOSITORY_URL', 'https://upload.pypi.org/legacy/')

    if not os.path.exists(directories['packages']):
        print(f'Package directory {directories["packages"]!r} does not exist, no packages to publish', flush=True)
        return 0

    if not env_bool('PUBLISH_PYTHON', True):
        print('Publish is disabled, skipping publish operation', flush=True)
        return 0

    if not env_bool('PUBLISH', True):
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

    if not os.path.exists(twine_command):  # pragma: no cover
        print('The twine command is missing', flush=True)
        return 1

    print(f'\n# Publishing to {twine_repository_url} as user {user}', flush=True)

    package_name = setup_query('--name')
    published = []
    failed = []
    for filename in os.listdir(directories['packages']):
        print(f'\tUploading {filename}', flush=True)
        command = [twine_command, 'upload', '--verbose', os.path.join(directories['packages'], filename)]

        os.environ['TWINE_USERNAME'] = user
        os.environ['TWINE_PASSWORD'] = password
        os.environ['TWINE_REPOSITORY_URL'] = twine_repository_url
       
        print(f'\tRunning: {" ".join(command)}')
        log_filename = os.path.join(directories['logs'], f'twine_{filename}.log')
        with open(log_filename, 'ab') as output_handle:
            try:
                subprocess.check_call(command, stdout=output_handle, stderr=subprocess.STDOUT)  # nosec
                published.append(filename)
            except subprocess.CalledProcessError as error:
                print(f'\tUpload of package file {filename!r} failed, returncode {error.returncode}', flush=True)
                output_handle.write(f'Upload of package file {filename!r} failed, returncode {error.returncode}'.encode(errors='ignore'))
                failed.append(filename)
                if error.stdout:
                    output_handle.write(error.stdout)
                if error.stderr:
                    output_handle.write(error.stderr)

    endpoint = twine_repository_url.rstrip('/')
    if endpoint.endswith('/legacy'):
        endpoint = endpoint[:-7] + '/simple'
    if endpoint.startswith('https://upload.'):
        endpoint = f'https://{endpoint[15:]}'

    publish_failed: List[str] = []
    if publish_timeout:
        print(f'\n# Polling {endpoint}/{package_name}/ for updated pacakge')
        publish_failed = list(poll_until_available(package_name, set(published), endpoint=endpoint, timeout=publish_timeout))

    if publish_failed:  # pragma: no cover
        failed += publish_failed

    if failed:
        update_job_status(status='FAILURE', message=f'{len(failed)} packages failed')
        return len(failed)

    return 0


if __name__ == '__main__':
    sys.exit(main())
