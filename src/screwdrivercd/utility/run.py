# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Command execution utilities
"""
import os
import subprocess  # nosec
from typing import List


def run_and_log_output(command: List[str], logfile: str, print_errors: bool=True):
    """
    Run a command with subprocess.check_output and send the output to the console and the specified logfile

    Parameters
    ----------
    command: list of str
        The parsed command to execute

    logfile: str
        The full path to the logfile to hold the output

    Raises
    ------
    subprocess.CalledProcessError - The command failed
    """
    log_dir = os.path.dirname(logfile)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    with open(logfile, 'wb') as fh:
        print(f'Running command: {" ".join(command)}', flush=True)
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)  # nosec
            fh.write(output)
        except subprocess.CalledProcessError as error:
            print(f'Command {command!r} failed', flush=True)
            fh.write(error.stdout)
            if print_errors and error.stdout:  # pragma: no cover
                print(error.stdout)
            raise error
