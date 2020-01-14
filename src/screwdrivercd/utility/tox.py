# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd tox helpers
"""
import logging
import os
import shutil
import subprocess  # nosec


logger = logging.getLogger(__name__)


def store_tox_logs():
    """
    Store tox logs into the Screwdriver artifacts
    """
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    if not artifacts_dir:
        return

    if artifacts_dir and os.path.exists('.tox'):
        log_dir = os.path.join(artifacts_dir, 'logs/tox')
        os.makedirs(log_dir, exist_ok=True)
        for dirpath, dirnames, filenames in os.walk('.tox'):
            if len(dirpath) < 5:
                continue
            if dirpath.endswith('/log'):
                for filename in filenames:
                    source_filename = os.path.join(dirpath, filename)
                    dest_dir = os.path.join(log_dir, dirpath[5:])
                    dest_filename = os.path.join(dest_dir, filename)
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copyfile(source_filename, dest_filename)


def run_tox(tox_envlist=None, tox_args=None):
    """
    Run tox
    """
    command = []

    # Use stdbuf to line buffer output if it is present
    if shutil.which('stdbuf'):  # pragma: no cover
        command += ['stdbuf', '-oL', '-eL']

    if shutil.which('pypirun'):  # pragma: no cover
        command += ['pypirun', 'tox']

    command += ['tox']

    if not tox_args:
        tox_args = os.environ.get('TOX_ARGS', '').split()
    if tox_envlist:
        command += ['-e', tox_envlist]
    if tox_args:
        command += tox_args

    # Run command
    rc = 0
    logger.debug(f'Running: {" ".join(command)}')
    try:
        subprocess.check_call(command)  # nosec
    except subprocess.CalledProcessError as error:
        rc = error.returncode

    store_tox_logs()

    return rc
