#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import json
import logging
logging.basicConfig(level=logging.DEBUG)
import unittest
from screwdrivercd.installdeps.config import Configuration
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory


TEST_CONFIG = '''[build-system]
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'yinst', 'yum', 'pip3']

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
        repos = {}

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
        repos = {}
'''

class TestConfig(unittest.TestCase):
    def setUp(self):
        super(TestConfig, self).setUp()

    def test__configuration__defaults__no_config(self):
        with InTemporaryDirectory():
            result = Configuration()
            self.assertListEqual(result.configuration['apk']['deps'], [])
            self.assertListEqual(result.configuration['apt-get']['deps'], [])
            self.assertListEqual(result.configuration['install'], ['apk', 'apt-get', 'yinst', 'yum', 'pip3'])
            self.assertListEqual(result.configuration['yinst']['deps'], [])
            self.assertListEqual(result.configuration['yum']['deps'], [])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

    def test__configuration__no_tool_configs(self):
        with InTemporaryDirectory():
            with open('pyproject.toml', 'w') as file_handle:
                file_handle.write('[build-system]\nrequires = ["setuptools", "wheel"]  # PEP 508 specifications.')
            result = Configuration('pyproject.toml')
            self.assertListEqual(result.configuration['apk']['deps'], [])
            self.assertListEqual(result.configuration['apt-get']['deps'], [])
            self.assertListEqual(result.configuration['install'], ['apk', 'apt-get', 'yinst', 'yum', 'pip3'])
            self.assertListEqual(result.configuration['yinst']['deps'], [])
            self.assertListEqual(result.configuration['yum']['deps'], [])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

    def test__configuration__invalid_filename(self):
        with InTemporaryDirectory():
            with open('pyproject.toml', 'w') as file_handle:
                file_handle.write('[build-system]\nrequires = ["setuptools", "wheel"]  # PEP 508 specifications.')
            result = Configuration('pyprojectt.toml')
            self.assertListEqual(result.configuration['apk']['deps'], [])
            self.assertListEqual(result.configuration['apt-get']['deps'], [])
            self.assertListEqual(result.configuration['install'], ['apk', 'apt-get', 'yinst', 'yum', 'pip3'])
            self.assertListEqual(result.configuration['yinst']['deps'], [])
            self.assertListEqual(result.configuration['yum']['deps'], [])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

    def test__configuration__no_sdv4_installdeps_configs(self):
        with InTemporaryDirectory():
            with open('pyproject.toml', 'w') as file_handle:
                file_handle.write('[build-system]\nrequires = ["setuptools", "wheel"]  # PEP 508 specifications.\n[tool.foo]\ninstall = ["apk", "apt-get", "yinst", "yum", "pip3"]')
            result = Configuration()
            self.assertListEqual(result.configuration['apk']['deps'], [])
            self.assertListEqual(result.configuration['apt-get']['deps'], [])
            self.assertListEqual(result.configuration['install'], ['apk', 'apt-get', 'yinst', 'yum', 'pip3'])
            self.assertListEqual(result.configuration['yinst']['deps'], [])
            self.assertListEqual(result.configuration['yum']['deps'], [])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

    def test__configuration__test__deps(self):
        with InTemporaryDirectory():
            with open('pyproject.toml', 'w') as file_handle:
                file_handle.write(TEST_CONFIG)
            result = Configuration()
            self.assertListEqual(result.configuration['apk']['deps'], ['python3', 'mysql-client'])
            self.assertListEqual(result.configuration['apt-get']['deps'], ['python3', 'mysql-client'])
            self.assertListEqual(result.configuration['yinst']['deps'], ['python36', 'dist_utils'])
            self.assertListEqual(result.configuration['yum']['deps'], ['yahoo_python36;distro_version<"7.5', 'yahoo_python37;distro_version>="7.5"', 'mysql;distro_version<"7"', 'mariadb;distro_version>="7"'])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

    def test__configuration__test__deps__scrwdrivercd_installdeps(self):
        with InTemporaryDirectory():
            with open('pyproject.toml', 'w') as file_handle:
                file_handle.write(TEST_CONFIG.replace('sdv4_installdeps', 'screwdrivercd_installdeps'))
            result = Configuration()
            self.assertListEqual(result.configuration['apk']['deps'], ['python3', 'mysql-client'])
            self.assertListEqual(result.configuration['apt-get']['deps'], ['python3', 'mysql-client'])
            self.assertListEqual(result.configuration['yinst']['deps'], ['python36', 'dist_utils'])
            self.assertListEqual(result.configuration['yum']['deps'], ['yahoo_python36;distro_version<"7.5', 'yahoo_python37;distro_version>="7.5"', 'mysql;distro_version<"7"', 'mariadb;distro_version>="7"'])
            self.assertListEqual(result.configuration['pip3']['deps'], [])

if __name__ == '__main__':
    unittest.main()
