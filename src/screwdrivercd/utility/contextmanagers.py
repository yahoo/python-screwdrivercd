# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver Utility ContextManagers
"""
import logging
import os
import signal
from contextlib import contextmanager, ContextDecorator
from datetime import timedelta
from tempfile import TemporaryDirectory
from typing import Optional, Union

from .exceptions import TimeoutError


logger = logging.getLogger(__name__)


@contextmanager
def working_dir(new_path):
    """
    A context manager that changes to the new_path directory and
    returns to the current working directory when it completes.
    """
    old_dir = os.getcwd()
    os.chdir(new_path)
    try:
        yield new_path
    finally:
        os.chdir(old_dir)


@contextmanager
def revert_file(filename):  # pragma: no cover
    """
    A context manager that reverts a file's contents.
    """
    original_data = None
    exists = os.path.exists(filename)
    if exists:
        with open(filename, 'rb') as file_handle:
            original_data = file_handle.read()

    try:
        yield filename
    finally:
        if exists:
            if original_data:
                with open(filename, 'wb') as file_handle:
                    file_handle.write(original_data)
        else:
            if os.path.exists(filename):
                os.remove(filename)


@contextmanager
def InTemporaryDirectory(suffix=None, prefix=None, dir=None):
    """
    A context manager that creates a temporary directory and switches into it
    """
    with TemporaryDirectory(suffix=suffix, prefix=prefix, dir=dir) as tempdir:
        with working_dir(tempdir):
            yield tempdir


class Timeout(ContextDecorator):
    """
    A contextmanager that will timeout after a specific datetime.timedelta
    """
    use_alarm: Union[bool, None] = False
    _old_handler = None

    def __init__(self, timeout: Optional[timedelta]=None, use_alarm: Union[bool, None]=None):
        self.timeout = timeout
        self.use_alarm = use_alarm
        if use_alarm is None:
            # use_alarm wasn't specified, set the value based on support for signal.setitimer()
            if hasattr(signal, 'setitimer'):
                self.use_alarm = False
            else:  # pragma: no cover
                self.use_alarm = True

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f'Timeout after {self.timeout}')

    def __enter__(self):
        if self.timeout:
            if self.use_alarm:
                self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(self.timeout.seconds)
            else:
                self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, float(self.timeout.microseconds) / 1000000)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timeout:
            if self.use_alarm:
                signal.alarm(0)
            else:
                signal.setitimer(signal.ITIMER_REAL, 0)
        if self._old_handler:
            signal.signal(signal.SIGALRM, self._old_handler)
