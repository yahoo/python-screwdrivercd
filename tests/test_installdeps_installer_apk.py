#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import tempfile
import unittest.mock

from screwdrivercd.installdeps.installers.apk import ApkInstaller


CONFIG_FILE = 'pyproject.toml'
TEST_CONFIG = f'''[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
    install = ['apk']

    [tool.sdv4_installdeps.apk]
        deps = [
            'python3',
            'mysql-client'
        ]

'''


class TestApk(unittest.TestCase):
    original_environ = None

    def setUp(self):
        self._cwd = os.getcwd()
        super().setUp()
        self.original_environ = os.environ
        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)
        with open(CONFIG_FILE, 'w') as config_handle:
            config_handle.write(TEST_CONFIG)

    def tearDown(self):
        super().tearDown()
        if self.original_environ:
            os.environ = self.original_environ
            self.original_environ = None
        os.chdir(self._cwd)
        self.tempdir.cleanup()

    @unittest.skipUnless(os.path.exists('/sbin/apk'), 'No apk binary present on system')
    def test__install__default(self):
        installer = ApkInstaller(dry_run=True)
        result = installer.install_dependencies()
        self.assertIn('python3', result)
