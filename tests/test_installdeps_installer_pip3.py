#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import tempfile
import unittest.mock
import subprocess
import sys

import distro
from pypirun.cli import interpreter_parent
from screwdrivercd.installdeps.installers.pip3 import PipInstaller
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory


CONFIG_FILE = 'pyproject.toml'
TEST_CONFIG = f'''[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'yinst', 'yum', 'pip3']

    [tool.sdv4_installdeps.pip3]
        deps = [
            'serviceping',
            'safety;distro_version=="{distro.version()}"', 'pypirun;distro_version!="{distro.version()}"'
        ]
'''


class TestPip3(unittest.TestCase):
    original_environ = None

    def setUp(self):
        self._cwd = os.getcwd()
        super().setUp()
        self.original_environ = os.environ
        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)
        with open(CONFIG_FILE, 'w') as config_handle:
            config_handle.write(TEST_CONFIG)
        self.venv_dir = os.path.join(self.tempdir.name, 'venv')
        self.venv_bin_dir = os.path.join(self.venv_dir, 'bin')
        interpreter = interpreter_parent(sys.executable)
        subprocess.check_call([interpreter, '-m', 'venv', self.venv_dir])

    def tearDown(self):
        super().tearDown()
        if self.original_environ:
            os.environ = self.original_environ
            self.original_environ = None
        os.chdir(self._cwd)
        self.tempdir.cleanup()

    def test__install__default(self):
        installer = PipInstaller(bin_dir=self.venv_bin_dir)
        result = installer.install_dependencies()
        os.system(f'ls -lR {os.path.join(self.tempdir.name, "venv")}/bin')
        self.assertListEqual(result, ['serviceping', 'safety'])
        expected_command = os.path.join(self.tempdir.name, 'venv/bin/serviceping')
        self.assertTrue(os.path.exists(expected_command), f'Command not found {expected_command!r}')
        expected_command = os.path.join(self.tempdir.name, 'venv/bin/safety')
        self.assertTrue(os.path.exists(expected_command), f'Command not found {expected_command!r}')
        expected_command = os.path.join(self.tempdir.name, 'venv/bin/pypirun')
        self.assertFalse(os.path.exists(expected_command), f'Command found {expected_command!r}')

