# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver Utility Runtime environment functions
"""
import logging
import os
import sys
from typing import Dict, Union

from pypirun.cli import interpreter_parent


logger = logging.getLogger(__name__)


def env_bool(variable_name: str, default: Union[None, bool] = None) -> Union[None, bool]:
    """
    Return the value of an env variable as a boolean

    Parameters
    ----------
    variable_name: str
        The environment variable

    default: bool, optional
        The default value to return if the env variable is not present.  Default=None

    Returns
    -------
    bool or None:
        The value from the env variable if present, otherwise the default value.

    """
    true_strings = ['true', 'on', '1']

    if variable_name not in os.environ.keys():
        return default

    value = os.environ.get(variable_name, str(default)).lower()

    if value in true_strings:
        return True

    return False


def env_int(variable_name: str, default: int = 0) -> int:
    """
    Return the value of an environment variable as an integer

    Parameters
    ----------
    variable_name: str
        Name of the environment variable

    default: int
        Default value to return if the environment variable is not present

    Returns
    -------
    int:
        Value of the env variable as an integer, or the default value if the env variable is not present.
    """
    if variable_name not in os.environ.keys():
        return default

    value = os.environ.get(variable_name, str(default)).lower()
    return int(value)


def flush_terminals():
    """
    Flush the terminal devices
    """
    sys.stdout.flush()
    sys.stderr.flush()


def interpreter_bin_command(command: str='', fallback_path: bool=True) -> str:
    """
    Return the full path to a command in the current interpreter's bin directory.

    This command handles finding the bin directory, even if the interpreter is running within a virtualenv

    Parameters
    ----------
    command: str, optional
        The command to find in the interpreter bin directory, default=python

    Returns
    -------
    str:
        Full path to the command.  If the command is not present returns command if fallback_path is True or an empty
        string otherwise.
    """
    if not command:
        command = os.path.basename(sys.executable)
    bin_dir = os.path.dirname(sys.executable)
    new_command = os.path.join(bin_dir, command)
    if os.path.exists(new_command):
        return new_command
    bin_dir = os.path.dirname(interpreter_parent(sys.executable))
    new_command = os.path.join(bin_dir, command)
    if os.path.exists(new_command):  # pragma: no cover
        return new_command
    if fallback_path:
        return command
    return ''


def standard_directories(command: str='') -> Dict[str, str]:
    """
    Dictionary of standard directory locations for a command

    Parameters
    ----------
    command: str, optional
        The name of the command to get the directories for, if no command is given the base directory will be used

    Returns
    -------
    dict of str
        A dictionary of directory types and paths
    """
    sep = ''
    if command:
        sep = os.sep

    artifacts_dir: str = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    directories: Dict[str, str] = {
        'artifacts': artifacts_dir,
        'documentation': os.path.join(artifacts_dir, f'documentation'),
        'logs': os.path.join(artifacts_dir, f'logs{sep}{command}'),
        'packages': os.path.join(artifacts_dir, f'packages'),
        'reports': os.path.join(artifacts_dir, f'reports{sep}{command}'),
    }
    for directory in directories.values():
        if directory:  # pragma: no cover
            os.makedirs(directory, exist_ok=True)

    return directories


def ins_filename(filename: str) -> str:
    """
    Return the filename of an actual file or directory that case insensitively resolves to the filename given.  If no
    matching files or directories exists, returns an empty string.
    """
    contain_dir = os.path.dirname(filename)
    base_name = os.path.basename(filename).lower()
    if not contain_dir:
        contain_dir = '.'
    if not os.path.exists(contain_dir):
        return ''
    for f in os.listdir(contain_dir):
        if base_name == f.lower():
            if os.path.dirname(filename):
                return os.path.join(os.path.dirname(filename), f)
            else:
                return f
    return ''


def is_pull_request() -> bool:
    """
    Return True if the SD_PULL_REQUEST environment variable has a PULL Request value, False otherwise
    """
    pr_num_str = os.environ.get('SD_PULL_REQUEST', '')
    if not pr_num_str:
        return False

    try:
        pr_num = int(pr_num_str)
    except ValueError:
        return False

    return True
