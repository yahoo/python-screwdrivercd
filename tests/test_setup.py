# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
test_setup
----------

Tests for the 'yahoo.platform_version.setup' module.
"""
import os
import unittest
from tempfile import TemporaryDirectory
from screwdrivercd.version.setup import setupcfg_has_metadata


class TestSetup(unittest.TestCase):

    environ_backup = None
    origcwd = os.getcwd()

    def setUp(self):
        # Save os.environ values we may need to change
        environ_backup = {}
        for key in ['BUILD_NUMBER', 'JOB_TYPE', 'SD_PULL_REQUEST']:
            environ_backup[key] = os.environ.get(key, None)
        self.tempdir = TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        # Restore the os.environ values in case they were changed
        if self.environ_backup:
            for key, value in self.environ_backup:
                if value is None:
                    del os.environ[key]
                else:
                    os.environ[key] = value
        self.environ_backup = None
        os.chdir(self.origcwd)
        self.tempdir.cleanup()

    def test__setupcfg_has_metadata__true(self):
        with open('setup.cfg', 'w') as setup_cfg_handle:
            setup_cfg_handle.write('[metadata]\nversion = 1.2.3\n\n')
        self.assertTrue(setupcfg_has_metadata())

    def test__setupcfg_has_metadata__false(self):
        with open('setup.cfg', 'w') as setup_cfg_handle:
            setup_cfg_handle.write('[foo]\nversion = 1.2.3\n\n')
        self.assertFalse(setupcfg_has_metadata())

    def test__setupcfg_has_metadata__missing(self):
        self.assertFalse(setupcfg_has_metadata())


if __name__ == '__main__':
    unittest.main()
