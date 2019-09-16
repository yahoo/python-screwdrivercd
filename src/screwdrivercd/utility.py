# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd utility functions
"""
import logging
import os
import subprocess  # nosec
import sys
from contextlib import contextmanager
from typing import Optional


logger = logging.getLogger(__name__)


# Use termcolor if it's installed
try:
    from termcolor import colored
except ImportError:
    logger.debug('Termcolor is not installed')
    def colored(text, color):
        return text


def create_artifact_directory(artifact_directory: Optional[str]=''):
    """
    Create the artifact directory if it is not present

    Parameters
    ----------
    artifact_directory: str, optional
        The artifact destination directory to create, if not specified will use the value of the SD_ARTIFACTS_DIR
        environment variable, if the variable is not present it will use a directory named `artifacts`
    """
    if not artifact_directory:
        artifact_directory = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    if not os.path.exists(artifact_directory):
        os.makedirs(artifact_directory, exist_ok=True)


def env_bool(variable_name: str, default: Optional[bool]=True) -> bool:
    true_strings = ['true', 'on', '1']

    value = os.environ.get(variable_name, str(default)).lower()

    if value in true_strings:
        return True
    return False


def env_int(variable_name:str, default: Optional[int]=0) -> int:
    value = os.environ.get(variable_name, str(default)).lower()
    return int(value)


def flush_terminals():
    sys.stdout.flush()
    sys.stderr.flush()


def run_exit_on_error(command, show_output=False):
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        output = subprocess.check_output(command)  # nosec
    except subprocess.CalledProcessError as error:
        print(error.output.decode(errors='ignore'), file=sys.stderr, flush=True)
        print(str(error), file=sys.stderr, flush=True)
        sys.exit(1)
    if show_output:
        print(output.decode(errors='ignore'), flush=True)


def store_artifacts(artifact_dirs=None):
    dest = os.environ['ARTIFACTS_DIR']
    if not artifact_dirs:
        artifact_dirs = []

    if not artifact_dirs:
        if os.path.exists('artifacts'):
            artifact_dirs.append('artifacts')

    for artifact_dir in artifact_dirs:
        os.system(f'cp -r {artifact_dir}/* {dest}')  # nosec


@contextmanager
def working_dir(new_path):
    """
    A context manager that changes to the new_path directory and
    returns to the current working directory when it completes.
    """
    old_dir = os.getcwd()
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(old_dir)
