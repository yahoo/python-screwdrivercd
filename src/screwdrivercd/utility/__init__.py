"""
screwdrivercd utility functions
"""
import logging
import os
import sys
from contextlib import contextmanager
from typing import Union


logger = logging.getLogger(__name__)


def create_artifact_directory(artifact_directory: str = ''):
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
    artifact_directory = str(artifact_directory)
    if not os.path.exists(artifact_directory):
        os.makedirs(artifact_directory, exist_ok=True)


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
