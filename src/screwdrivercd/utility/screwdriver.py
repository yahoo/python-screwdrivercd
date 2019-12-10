# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd utility functions
"""
import os


def create_artifact_directory(artifact_directory: str = '') -> None:
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
    os.makedirs(artifact_directory, exist_ok=True)
