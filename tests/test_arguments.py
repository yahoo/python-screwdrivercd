# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import sys
import unittest
from tempfile import TemporaryDirectory
from screwdrivercd.version.arguments import get_config_default, parse_arguments
from screwdrivercd.version.exceptions import VersionError


class TestArguments(unittest.TestCase):
    orig_argv = None
    origcwd = os.getcwd()

    def setUp(self):
        self.orig_argv = sys.argv
        self.tempdir = TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        if self.orig_argv:
            sys.argv = self.orig_argv
        os.chdir(self.origcwd)
        self.tempdir.cleanup()

    def test__parse_arguments__default(self):
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertFalse(result.force_update)
        self.assertEqual(result.version_type, 'default')

    def test__parse_arguments__force_update(self):
        sys.argv = ['screwdrivercd_version', '--force_update']
        result = parse_arguments()
        self.assertTrue(result.force_update)
        self.assertEqual(result.version_type, 'default')

    def test__get_config_default__no_setup_cfg(self):
        result = get_config_default('version_type')
        self.assertIsNone(result)

    def test__get_config_default__setup_cfg__key_missing__default(self):
        result = get_config_default('version_type', 'default')
        self.assertEqual(result, 'default')

    def test__parse_arguments__default__setup_cfg__version_type__none(self):
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertEqual(result.version_type, 'default')

    def test__parse_arguments__default__setup_cfg__version_type(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[screwdrivercd.version]\nversion_type = utc_date\n')
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertEqual(result.version_type, 'utc_date')

    def test__parse_arguments__default__setup_cfg__version_type__invalid(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[screwdrivercd.version]\nversion_type = invalid\n')
        sys.argv = ['screwdrivercd_version']
        with self.assertRaises(VersionError):
            parse_arguments()

    def test__parse_arguments__setup_cfg__update_meta__true(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[screwdrivercd.version]\nupdate_screwdriver_meta = True\n')
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertTrue(result.update_meta)

    def test__parse_arguments_legacy__default__setup_cfg__version_type(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[sdv4.version]\nversion_type = utc_date\n')
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertEqual(result.version_type, 'utc_date')

    def test__parse_arguments_legacy__default__setup_cfg__version_type__invalid(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[sdv4.version]\nversion_type = invalid\n')
        sys.argv = ['screwdrivercd_version']
        with self.assertRaises(VersionError):
            parse_arguments()

    def test__parse_arguments_legacy__setup_cfg__update_meta__true(self):
        with open('setup.cfg', 'w') as fh:
            fh.write('[sdv4.version]\nupdate_screwdriver_meta = True\n')
        sys.argv = ['screwdrivercd_version']
        result = parse_arguments()
        self.assertTrue(result.update_meta)

