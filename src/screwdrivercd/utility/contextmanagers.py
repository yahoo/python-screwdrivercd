# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver Utility ContextManagers
"""
import logging
import os
from contextlib import contextmanager
from tempfile import TemporaryDirectory


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
        yield
    finally:
        os.chdir(old_dir)


@contextmanager
def revert_file(filename):
    """
    A context manager that reverts a file's contents.
    """
    original_data = None
    with open(filename, 'rb') as file_handle:
        original_data = file_handle.read()

    try:
        yield
    finally:
        if original_data:
            with open(filename, 'wb') as file_handle:
                file_handle.write(original_data)

@contextmanager
def InTemporaryDirectory():
    """
    A context manager that creates a temporary directory and switches into it
    """
    with TemporaryDirectory() as tempdir:
        with working_dir(tempdir):
            yield
