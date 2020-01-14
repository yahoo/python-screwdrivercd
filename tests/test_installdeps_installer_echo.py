#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import unittest
import unittest.mock

import distro
from screwdrivercd.installdeps.installer import Installer
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory

from . import ScrewdriverTestCase


CONFIG_FILE = 'pyproject.toml'
TEST_CONFIG = f'''[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
install = ['echo']

[tool.sdv4_installdeps.echo]
deps = ['python3', 'foo;distro_version=="{distro.version()}"', 'bar;distro_version!="{distro.version()}"']
'''

TEST_CONFIG_NODEPS = f'''[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
install = ['echo']

[tool.sdv4_installdeps.echo]
deps = []
'''

class TestEcho(ScrewdriverTestCase):

    installer_class = Installer

    def setUp(self):
        super().setUp()
        with open(CONFIG_FILE, 'w') as config_handle:
            config_handle.write(TEST_CONFIG)
        self.installer = Installer(bin_dir='/bin')

    def test__echo__has_dependencies(self):
        result = self.installer.has_dependencies
        self.assertEqual(result, True)

    def test__echo__is_supported(self):
        result = self.installer.is_supported
        self.assertEqual(result, True)

    def test__echo__install__nodeps(self):
        with open(CONFIG_FILE, 'w') as config_handle:
            config_handle.write(TEST_CONFIG_NODEPS)
        self.installer = Installer(bin_dir='/bin')
        result = self.installer.install_dependencies()
        self.assertListEqual(result, [])

    def test__echo__install__default_python(self):
        result = self.installer.install_dependencies()
        self.assertListEqual(result, ['python3', 'foo'])

    def test__echo__install__default_python__dry_run(self):
        installer = self.installer_class(dry_run=True)
        result = installer.install_dependencies()
        self.assertListEqual(result, ['python3', 'foo'])

    def test__echo__invalid_dependencies(self):
        with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
            result = self.installer.install_dependencies()
            self.assertListEqual(result, [])

    def test__echo__install__invalid_deps(self):
        with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
            result = self.installer.install_dependencies()
            self.assertListEqual(result, [])

    def test__echo__install__invalid_deps__log_output(self):
        with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
            self.installer.print_output = False
            result = self.installer.install_dependencies()
            self.assertListEqual(result, [])

    def test__echo__install__invalid_deps__exit_on_missing(self):
        with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
            self.installer.exit_on_missing = True
            result = self.installer.install_dependencies()
            self.assertListEqual(result, [])

    def test__determine_bin_directory__install_command_path(self):
        self.installer.install_command[0] = 'echo'
        self.installer.bin_dir = None
        self.installer.install_command_path = ['/bin']
        self.installer.determine_bin_directory()

    def test__determine_bin_directory__system_path(self):
        self.installer.install_command[0] = 'echo'
        self.installer.bin_dir = None
        self.installer.install_command_path = []
        self.installer.use_system_path = True
        self.installer.determine_bin_directory()

    def test_find_install_command__bin_dir(self):
        self.installer.install_command[0] = 'echo'
        self.installer.bin_dir = '/bin'
        self.installer.install_command_path = []
        self.installer.find_install_command()
        self.assertEqual(self.installer.install_command[0], '/bin/echo')

    def test_find_install_command__system_dir(self):
        self.installer.install_command[0] = 'echo'
        self.installer.bin_dir = None
        self.installer.install_command_path = []
        self.installer.use_system_path = True
        self.installer.find_install_command()
