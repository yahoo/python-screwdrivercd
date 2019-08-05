# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import configparser
import copy
import os
import sys
from tempfile import TemporaryDirectory
import unittest
from screwdrivercd.version import cli
from screwdrivercd.version.version_types import versioners


class TestCLI(unittest.TestCase):
    cwd = None
    orig_argv = None
    orig_environ =None
    tempdir = None
    environ_keys = set('SD_BUILD')
    origcwd = os.getcwd()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orig_argv = sys.argv
        self.cwd = os.getcwd()
        self.orig_environ = copy.copy(os.environ)

    def setUp(self):
        super().setUp()
        self.orig_argv = sys.argv
        self.tempdir = TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        super().tearDown()
        if self.orig_argv:
            sys.argv = self.orig_argv

        for environ_key in self.environ_keys:
            if self.orig_environ.get(environ_key, None):
                os.environ[environ_key] = self.orig_environ[environ_key]

        for versioner in versioners.values():
            versioner.ignore_meta_version = True
        os.chdir(self.origcwd)
        self.tempdir.cleanup()

    def _get_version(self, setup_cfg_filename='setup.cfg'):
        config = configparser.ConfigParser()
        config.read(setup_cfg_filename)
        if 'metadata' in config.sections():
            return config['metadata'].get('version', None)

    def test__main__no_setup_cfg(self):
        sys.argv = ['cli']
        cli.main()

    def test__main__setup_cfg__version(self):
        sys.argv = ['cli', '--ignore_meta']
        if 'SD_BUILD' in os.environ:
            del os.environ['SD_BUILD']
        print(f'current directory {os.getcwd()!r}')
        with open('setup.cfg', 'w') as fh:
            fh.write('[metadata]\nversion = 0.0.0\n[screwdrivercd.version]\nversion_type = git_revision_count\n')
        cli.main()
        with open('setup.cfg') as fh:
            result = fh.read()
        self.assertIn('version = 0.0.0', result)

    def test__main__setup_cfg__version__update_meta(self):
        sys.argv = ['cli', '--ignore_meta', '--update_meta']
        if 'SD_BUILD' in os.environ:
            del os.environ['SD_BUILD']
        print(f'current directory {os.getcwd()!r}')
        with open('setup.cfg', 'w') as fh:
            fh.write('[metadata]\nversion = 0.0.0\n[screwdrivercd.version]\nversion_type = git_revision_count\n')
        cli.main()
        with open('setup.cfg') as fh:
            result = fh.read()
        self.assertIn('version = 0.0.0', result)


if __name__ == '__main__':
    unittest.main()
