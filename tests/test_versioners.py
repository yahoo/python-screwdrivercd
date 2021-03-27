# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import datetime
import os
import subprocess  # nosec
import unittest
from . import ScrewdriverTestCase
from tempfile import NamedTemporaryFile

from screwdrivercd.version.exceptions import VersionError
from screwdrivercd.version.version_types import versioners, Version, VersionGitRevisionCount, VersionSDV4Build, VersionDateSDV4Build, VersionUTCDate, VersionManualUpdate


class TestVersioners(ScrewdriverTestCase):
    environ_keys = {
        'BASE_PYTHON', 'PACKAGE_DIR', 'PACKAGE_DIRECTORY', 'SD_ARTIFACTS_DIR', 'SD_BUILD', 'SD_BUILD_ID',
        'SD_PULL_REQUEST', 'SCM_URL', 'SD_BUILD_SHA',
    }

    def test__version__read_setup_version__no_version(self):
        version = Version(ignore_meta_version=True).read_setup_version()
        self.assertEqual(version, Version.default_version)

    def test__version__get_link_to_commit_using_hash__unset_env_variables(self):
        version = Version(ignore_meta_version=True, link_to_commit=True).get_link_to_commit_using_hash()
        self.assertEqual(version.get_link_to_commit_using_hash(), '')

    def test__version__get_link_to_commit_using_hash__set_and_unset_env_variables(self):
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        version = Version(ignore_meta_version=True, link_to_commit=True).get_link_to_commit_using_hash()
        self.assertEqual(version.get_link_to_commit_using_hash(), '')

    def test__version__get_link_to_commit_using_hash__set_env_variables(self):
        os.environ['SCM_URL'] = 'https://github.com'
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        version = Version(ignore_meta_version=True, link_to_commit=True).get_link_to_commit_using_hash()
        self.assertEqual(version.get_link_to_commit_using_hash(), 'https://github.com/commit/a5c3785ed8d6a35868bc169f07e40e889087fd2e')

    def test__manual_version_update(self):
        with NamedTemporaryFile('w') as file:
            setup_cfg_content = '[metadata]\nversion = 1.0.5'
            file.write(setup_cfg_content)

            file.seek(0)
            version = VersionManualUpdate(setup_cfg_filename=file.name, ignore_meta_version=True)
            self.assertEqual(version.generate(), ['1', '0', '5'])

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

    def test__sdv4_date(self):
        os.environ['SD_BUILD'] = '9999'
        now = datetime.datetime.utcnow()
        expected = f'{str(now.year)[-2:]}.{now.month}.{os.environ["SD_BUILD"]}'
        version = str(VersionDateSDV4Build(ignore_meta_version=True, now=now))
        self.assertEqual(version, expected)

    def test__sdv4_date__sd_build_id(self):
        os.environ['SD_BUILD_ID'] = '9999'
        now = datetime.datetime.utcnow()
        expected = f'{str(now.year)[-2:]}.{now.month}.{os.environ["SD_BUILD_ID"]}'
        version = str(VersionDateSDV4Build(ignore_meta_version=True, now=now))
        self.assertEqual(version, expected)

    def test__sdv4_date__pr(self):
        os.environ['SD_BUILD'] = '9999'
        os.environ['SD_PULL_REQUEST'] = '9'
        now = datetime.datetime.utcnow()
        expected = f'{str(now.year)[-2:]}.{now.month}.{os.environ["SD_BUILD"]}a{os.environ["SD_PULL_REQUEST"]}'
        version = str(VersionDateSDV4Build(ignore_meta_version=True, now=now))
        self.assertEqual(version, expected)

    def test__sdv4_date__unset(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        with self.assertRaises(VersionError):
            version = str(VersionDateSDV4Build(ignore_meta_version=True))


if __name__ == '__main__':
    unittest.main()
