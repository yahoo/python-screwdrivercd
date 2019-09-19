# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver environment functions
"""
import json
import logging
import os
from ..utility import env_bool
from .metadata import Metadata


def get_env_job_name(default='') -> str:
    """
    Get the job name from the scrwdriver environment that matches the name as reported to github

    Returns
    -------
    str:
        Job name, will be an empty string if a name is not present in the environment
    """
    job_name = os.environ.get('SD_JOB_NAME', default).split(':')[-1]
    # pr = os.environ.get('SD_PULL_REQUEST', '')
    # if pr:
    #     return f'PR:{job_name}'
    return job_name


def logging_basicConfig(**kwargs):
    """
    Call logging.basicConfig() with default values based on the screwdriver environment variables
    """
    level = kwargs.pop('level', None)
    check_prefix = kwargs.pop('check_prefix', '')
    if check_prefix and not level:
        kwargs['level'] = logging.DEBUG if env_bool(f'{check_prefix}_DEBUG', default=False) else logging.INFO
    return logging.basicConfig(**kwargs)


def update_job_status(status='SUCCESS', message='Everything looks good!'):
    """
    Update the job status in the screwdriver metadata

    Parameters
    ----------
    status: str, optional
        Must be SUCCESS or FAILURE

    message: str, optional
        The status message to use

    Raises
    ------
    KeyError: Status is not SUCCESS or FAILURE
    """
    if status not in ['SUCCESS', 'FAILURE']:
        raise KeyError(f'Status {status} not found in ["SUCCESS", "FAILURE"]')

    metadata = Metadata()
    metadata.set(f'meta.status.{get_env_job_name()}', json.dumps(dict(status=status, message=message)))
