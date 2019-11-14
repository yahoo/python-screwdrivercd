# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import pathlib
import tempfile
import unittest

from screwdrivercd.documentation.utility import clean_directory, copy_contents
from screwdrivercd.utility import env_bool

class UtilityTestCase(unittest.TestCase):
    used_env_vars = ['TEST_UTILITY_ENV_BOOL']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._pwd)

    def clear_used_env_keys(self):
        for varname in self.used_env_vars:
            if varname in os.environ.keys():
                del os.environ[varname]

    def test_clean_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            testfile = f'{tempdir}/testfile'
            pathlib.Path(testfile).touch()
            self.assertTrue(os.path.exists(testfile))
            clean_directory(tempdir)
            self.assertFalse(os.path.exists(testfile))

    def test_copy_contents(self):
        with tempfile.TemporaryDirectory() as sourcedir:
            with tempfile.TemporaryDirectory() as destdir:
                pathlib.Path(f'{sourcedir}/testfile').touch()
                self.assertFalse(os.path.exists(f'{destdir}/testfile'))
                copy_contents(sourcedir, destdir)
                self.assertTrue(os.path.exists(f'{destdir}/testfile'))

    def test_env_bool_default_true(self):
        self.assertTrue(env_bool('TEST_UTILITY_ENV_BOOL', True))

    def test_env_bool_default_false(self):
        self.assertFalse(env_bool('TEST_UTILITY_ENV_BOOL', False))

    def test_env_bool_true(self):
        os.environ['TEST_UTILITY_ENV_BOOL'] = 'True'
        self.assertTrue(env_bool('TEST_UTILITY_ENV_BOOL', False))

    def test_env_bool_false(self):
        os.environ['TEST_UTILITY_ENV_BOOL'] = 'False'
        self.assertFalse(env_bool('TEST_UTILITY_ENV_BOOL', True))
