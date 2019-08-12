# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import copy
import datetime
import os
import subprocess
import sys
import tempfile
import unittest
from screwdrivercd.version.exceptions import VersionError
from screwdrivercd.version.version_types import versioners, Version, VersionGitRevisionCount, VersionSDV4Build, VersionUTCDate


class TestVersioners(unittest.TestCase):
    cwd = None
    orig_argv = None
    orig_environ =None
    tempdir = None
    environ_keys = {'SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orig_argv = sys.argv
        self.cwd = os.getcwd()
        self.orig_environ = copy.copy(os.environ)
        os.environ['SD_PULL_REQUEST'] = ''

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        if self.orig_argv:
            sys.argv = self.orig_argv

        if self.cwd:
            os.chdir(self.cwd)

        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

        for environ_key in self.environ_keys:
            if self.orig_environ.get(environ_key, None):
                os.environ[environ_key] = self.orig_environ[environ_key]

    def delkeys(self, keys):
        for key in keys:
            if key in os.environ.keys():
                del key

    def setupEmptyGit(self):
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'config', 'user.email', 'foo@bar.com'])
        subprocess.check_call(['git', 'config', 'user.name', 'foo'])
        with open('setup.cfg', 'w') as setup_handle:
            setup_handle.write('')
        subprocess.check_call(['git', 'add', 'setup.cfg'])
        subprocess.check_call(['git', 'commit', '-a', '-m', 'initial'])

    def test__version__read_setup_version__no_version(self):
        version = Version(ignore_meta_version=True).read_setup_version()
        self.assertEqual(version, Version.default_version)

    def test__git_revision_count__no_git(self):
        with self.assertRaises(VersionError):
            version = str(VersionGitRevisionCount(ignore_meta_version=True, log_errors=False))

    def test__git_revision_count__git(self):
        try:
            self.setupEmptyGit()
        except subprocess.CalledProcessError:
            # Git cli not working
            return
        version = str(VersionGitRevisionCount(ignore_meta_version=True, log_errors=False))
        self.assertEqual(version, '0.0.1')
        with open('foo', 'w') as fh:
            fh.write('')
        subprocess.call(['git', 'add', 'foo'])
        subprocess.call(['git', 'commit', '-a', '-m', 'added foo'])
        version = str(VersionGitRevisionCount(ignore_meta_version=True, log_errors=False))
        self.assertEqual(version, '0.0.2')

    def test__git_revision_count__git_update(self):
        try:
            self.setupEmptyGit()
        except subprocess.CalledProcessError:
            # Git cli not working
            return
        versioner = VersionGitRevisionCount(ignore_meta_version=True, log_errors=False)
        versioner.update_setup_cfg_metadata()
        with open('setup.cfg') as setup_handle:
            result = setup_handle.read().strip()
        self.assertIn('version = 0.0.1', result)

    def test__sdv4_SD_BUILD__unset(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        os.system('printenv')
        with self.assertRaises(VersionError):
            version = str(VersionSDV4Build(ignore_meta_version=True, log_errors=False))

    def test__sdv4_SD_BUILD__set(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        os.environ['SD_BUILD'] = '9999'
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        self.assertEqual(str(versioner), '0.0.9999')
        versioner.update_setup_cfg_metadata()
        config_version = Version().read_setup_version()
        self.assertEqual(config_version, ['0', '0', '9999'])

    def test__sdv4_SD_BUILD__PR__unset(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        with self.assertRaises(VersionError):
            version = str(VersionSDV4Build(ignore_meta_version=True, log_errors=False))

    def test__sdv4_SD_BUILD__PR__set(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        os.environ['SD_BUILD'] = '9999'
        os.environ['SD_PULL_REQUEST'] = '9'
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        self.assertEqual(str(versioner), '0.0.9999a9')
        versioner.update_setup_cfg_metadata()
        config_version = Version().read_setup_version()
        self.assertEqual(config_version, ['0', '0', '9999a9'])

    def test__utc_date(self):
        now = datetime.datetime.utcnow()
        expected = '{now.year}.{now.month}{now.day:02}.{now.hour:02}{now.minute:02}{now.second:02}'.format(now=now)
        version = str(VersionUTCDate(ignore_meta_version=True, now=now))
        self.assertEqual(version, expected)


if __name__ == '__main__':
    unittest.main()
