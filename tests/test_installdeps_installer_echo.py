#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import unittest
import unittest.mock

import distro
from screwdrivercd.installdeps.installer import Installer
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory


CONFIG_FILE = 'pyproject.toml'
TEST_CONFIG = f'''[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'yum', 'pip3']

    [tool.sdv4_installdeps.apk]
        deps = [
            'python3',
            'mysql-client'
        ]

    [tool.sdv4_installdeps.apt-get]
        deps = [
            'python3',
            'mysql-client'
        ]

    [tool.sdv4_installdeps.echo]
        deps = ['python3', 'foo;distro_version=="{distro.version()}"', 'bar;distro_version!="{distro.version()}"']

    [tool.sdv4_installdeps.yum]
        repos.verizon_python_rpms = "https://edge.artifactory.yahoo.com:4443/artifactory/python_rpms/python_rpms.repo"
        deps = [
            'yahoo_python36;distro_version<"7.5',
            'yahoo_python37;distro_version>="7.5"',
            'mysql;distro_version<"7"',
            'mariadb;distro_version>="7"'
        ]

    [tool.sdv4_installdeps.yinst]
        deps = [
            'python36',
            'dist_utils'
        ]
        deps_stable = []
        deps_current = []
        deps_test = []
        deps_quarantine = []

    [tool.sdv4_installdeps.pip3]
        bin_dir = ''
        deps = []
'''


class TestEcho(unittest.TestCase):
    original_environ = None

    def setUp(self):
        super().setUp()
        self.original_environ = os.environ

    def tearDown(self):
        super().tearDown()
        if self.original_environ:
            os.environ = self.original_environ
            self.original_environ = None

    def test__echo__install__default_python(self):
        with InTemporaryDirectory():
            with open(CONFIG_FILE, 'w') as config_handle:
                config_handle.write(TEST_CONFIG)
            installer = Installer()
            result = installer.install_dependencies()
            self.assertListEqual(result, ['python3', 'foo'])

    def test__echo__install__default_python__dry_run(self):
        with InTemporaryDirectory():
            with open(CONFIG_FILE, 'w') as config_handle:
                config_handle.write(TEST_CONFIG)
            installer = Installer(dry_run=True)
            result = installer.install_dependencies()
            self.assertListEqual(result, ['python3', 'foo'])

    def test__echo__install__invalid_deps(self):
        with InTemporaryDirectory():
            with open(CONFIG_FILE, 'w') as config_handle:
                config_handle.write(TEST_CONFIG)
            with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
                installer = Installer()
                result = installer.install_dependencies()
                self.assertListEqual(result, [])

    def test__echo__install__invalid_deps__log_output(self):
        with InTemporaryDirectory():
            with open(CONFIG_FILE, 'w') as config_handle:
                config_handle.write(TEST_CONFIG)
            with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
                installer = Installer()
                installer.print_output = False
                result = installer.install_dependencies()
                self.assertListEqual(result, [])

    def test__echo__install__invalid_deps__exit_on_missing(self):
        with InTemporaryDirectory():
            with open(CONFIG_FILE, 'w') as config_handle:
                config_handle.write(TEST_CONFIG)
            with unittest.mock.patch.object(Installer, 'validate_dependency', return_value=False) as mock_method:
                installer = Installer()
                installer.exit_on_missing = True
                result = installer.install_dependencies()
                self.assertListEqual(result, [])