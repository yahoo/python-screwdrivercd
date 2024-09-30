# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import datetime
import os
import subprocess  # nosec
import unittest

from . import ScrewdriverTestCase
from tempfile import NamedTemporaryFile

from screwdrivercd.version.exceptions import VersionError
from screwdrivercd.version.version_types import Version, VersionGitRevisionCount, VersionSDV4Build, VersionDateSDV4Build, VersionUTCDate, VersionManualUpdate


existing_project_url_config_setupcfg = {
    'setup.cfg': b"""
[metadata]
author = Yahoo Python Platform Team
author_email = python@verizonmedia.com
name=mypyvalidator
project_urls = 
    Documentation = https://yahoo.github.io/mypyvalidator/
    Change Log = https://yahoo.github.io/python-screwdrivercd/changelog/
    CI Pipeline = https://cd.screwdriver.cd/pipelines/1
    Source = https://github.com/yahoo/mypyvalidator/tree/a5c3785ed8d6a35868bc169f07e40e889087fd2e
version=0.0.0

[options]
packages = find_namespace:
package_dir =
    =src

[options.packages.find]
where=src
"""
}

existing_project_url_config_pyprojecttoml = {
    'pyproject.toml': b"""
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypyvalidator"
authors = [
    {name = "Yahoo Python Platform Team", email = "python@verizonmedia.com"}
]
description = "GH Cloud Test 1"
version = "0.0.0"

[tool.sdv4_version]
version_type = "sdv4_SD_BUILD"
"""
}


class TestVersioners(ScrewdriverTestCase):
    environ_keys = {
        'BASE_PYTHON', 'GITHUB_RUN_ID', 'PACKAGE_DIR', 'PACKAGE_DIRECTORY', 'SD_ARTIFACTS_DIR', 'SD_BUILD', 'SD_BUILD_ID',
        'SD_PULL_REQUEST', 'SCM_URL', 'SD_BUILD_SHA',
    }

    def test__version__read_setup_version__no_version_noconfig_files(self):
        version = Version(ignore_meta_version=True).read_setup_version()
        self.assertEqual(version, Version.default_version)

    def test__version__read_setup_version__no_version_pyproject_file(self):
        with open('pyproject.toml', 'wb') as fh:
            fh.write(b'[build-system]\nbuild-backend = "setuptools.build_meta')
        version = Version(ignore_meta_version=True).read_setup_version()
        self.assertEqual(version, Version.default_version)

    def test__version__get_link_to_project_using_hash__unset_env_variables(self):
        link = Version(ignore_meta_version=True, link_to_project=True).get_link_to_project_using_hash()
        self.assertEqual(link, '')

    def test__version__get_link_to_project_using_hash__set_and_unset_env_variables(self):
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        link = Version(ignore_meta_version=True, link_to_project=True).get_link_to_project_using_hash()
        self.assertEqual(link, '')

    def test__version__get_link_to_project_using_hash__set_env_variables__https_git(self):
        os.environ['SCM_URL'] = 'https://github.com/org/project'
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        ver = Version(ignore_meta_version=True, link_to_project=True)
        link = ver.get_link_to_project_using_hash()
        self.assertEqual(link, 'https://github.com/org/project/tree/a5c3785ed8d6a35868bc169f07e40e889087fd2e')

        ver.update_setup_cfg_metadata()
        self.assertTrue(os.path.exists('setup.cfg'))
        with open('setup.cfg') as fh:
            setup_cfg = fh.read()
        self.assertIn(link, setup_cfg)

    def test__version__get_link_to_project_using_hash__set_env_variables__https_git__existing_project_urls(self):
        os.environ['SCM_URL'] = 'https://github.com/org/project'
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        self.write_config_files(existing_project_url_config_setupcfg)

        ver = Version(ignore_meta_version=True, link_to_project=True)
        link = ver.get_link_to_project_using_hash()
        self.assertEqual(link, 'https://github.com/org/project/tree/a5c3785ed8d6a35868bc169f07e40e889087fd2e')

        ver.update_setup_cfg_metadata()
        self.assertTrue(os.path.exists('setup.cfg'))
        with open('setup.cfg') as fh:
            setup_cfg = fh.read()
        self.assertIn(link, setup_cfg)
        self.assertIn('Documentation = https://yahoo.github.io/mypyvalidator/', setup_cfg)

    def test__version__get_link_to_project_using_hash__set_env_variables__ssh_git(self):
        os.environ['SCM_URL'] = 'git@github.com:org/project'
        os.environ['SD_BUILD_SHA'] = 'a5c3785ed8d6a35868bc169f07e40e889087fd2e'
        ver = Version(ignore_meta_version=True, link_to_project=True)
        link = ver.get_link_to_project_using_hash()
        self.assertEqual(link, 'https://github.com/org/project/tree/a5c3785ed8d6a35868bc169f07e40e889087fd2e')

        ver.update_setup_cfg_metadata()
        self.assertTrue(os.path.exists('setup.cfg'))
        with open('setup.cfg') as fh:
            setup_cfg = fh.read()
        self.assertIn(link, setup_cfg)

    def test__manual_version_update(self):
        with NamedTemporaryFile('w') as setupcfg_file:
            setup_cfg_content = '[metadata]\nversion = 1.0.5'
            setupcfg_file.write(setup_cfg_content)

            setupcfg_file.seek(0)
            version = VersionManualUpdate(setup_cfg_filename=setupcfg_file.name, ignore_meta_version=True)
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
        print(versioner.setup_cfg_filename, versioner.setup_cfg_format)
        versioner.update_setup_cfg_metadata()
        with open('setup.cfg') as setup_handle:
            result = setup_handle.read().strip()
        self.assertIn('version = 0.0.1', result)

    def test__sdv4_SD_BUILD__unset(self):
        self.delkeys(['SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'])
        with self.assertRaises(VersionError):
            version = str(VersionSDV4Build(ignore_meta_version=True, log_errors=False))

    def test__sdv4_SD_BUILD__set(self):
        os.environ['SD_BUILD'] = '9999'
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        self.assertEqual(str(versioner), '0.0.9999')
        versioner.update_setup_cfg_metadata()
        config_version = Version().read_setup_version()
        self.assertEqual(config_version, ['0', '0', '9999'])

    def test__sdv4_SD_BUILD__pyproject__set(self):
        os.environ['SD_BUILD'] = '10000'
        self.write_config_files(existing_project_url_config_pyprojecttoml)
        os.system('ls -l')
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        self.assertEqual(str(versioner), '0.0.10000')
        versioner.update_setup_cfg_metadata()
        version_obj = Version()
        config_version = version_obj.read_setup_version()
        self.assertEqual(version_obj.setup_cfg_format, 'toml')
        self.assertEqual(version_obj.setup_cfg_filename, 'pyproject.toml')
        with open('pyproject.toml') as fh:
            content = fh.read()
        self.assertIn('0.0.10000', content)
        self.assertEqual(config_version, ['0', '0', '10000'])

    def test__sdv4_GITHUB_RUN_ID_toml_set(self):
        os.environ['GITHUB_RUN_ID'] = '9999'
        if os.path.exists('setup.cfg'):
            os.remove('setup.cfg')
        self.write_config_files(existing_project_url_config_pyprojecttoml)
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        self.assertEqual(str(versioner), '0.0.9999')
        self.assertEqual('toml', versioner.setup_cfg_format)
        versioner.update_setup_cfg_metadata()
        versioner = VersionSDV4Build(ignore_meta_version=True, log_errors=False)
        config_version = Version().read_setup_version()
        self.assertEqual(config_version, ['0', '0', '9999'])
        with open('pyproject.toml') as fh:
            content = fh.read()
        self.assertIn('0.0.9999', content)

    def test__sdv4_SD_BUILD__PR__unset(self):
        os.environ['SD_PULL_REQUEST'] = '1'
        with self.assertRaises(VersionError):
            version = str(VersionSDV4Build(ignore_meta_version=True, log_errors=False))

    def test__sdv4_SD_BUILD__PR__set(self):
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

    def test_get_env_single_var(self):
        os.environ['TEST_ENV_VAR'] = 'test_value'
        version = Version()
        result = version.get_env('TEST_ENV_VAR')
        self.assertEqual(result, 'test_value')

    def test_get_env_multiple_vars(self):
        os.environ['TEST_ENV_VAR1'] = 'value1'
        os.environ['TEST_ENV_VAR2'] = 'value2'
        version = Version()
        result = version.get_env(['TEST_ENV_VAR1', 'TEST_ENV_VAR2'])
        self.assertEqual(result, 'value1')

    def test_get_env_default_value(self):
        version = Version()
        result = version.get_env('NON_EXISTENT_VAR', 'default_value')
        self.assertEqual(result, 'default_value')

    def test_setup_cfg_format_with_setup_cfg(self):
        with open('setup.cfg', 'w') as f:
            f.write('[metadata]\nversion = 0.0.1')
        version = Version()
        self.assertEqual(version.setup_cfg_format, 'setupcfg')
        os.remove('setup.cfg')

    def test_setup_cfg_format_with_pyproject_toml(self):
        if os.path.exists('setup.cfg'):
            os.remove('setup.cfg')
        with open('pyproject.toml', 'w') as f:
            f.write('[tool.sdv4_version]\nversion_type = "sdv4_SD_BUILD"\n[project]\nversion="0.0.0"\n')
        version = Version()
        self.assertEqual(version.setup_cfg_filename, 'pyproject.toml')
        self.assertEqual(version.setup_cfg_format, 'toml')
        os.remove('pyproject.toml')

    def test_setup_cfg_format_with_pyproject_toml_no_version(self):
        if os.path.exists('setup.cfg'):
            os.remove('setup.cfg')
        with open('pyproject.toml', 'w') as f:
            f.write('[tool.sdv4_version]\nversion_type = "sdv4_SD_BUILD"\n')
        version = Version()
        self.assertEqual(version.setup_cfg_format, 'setupcfg')
        self.assertEqual(version.setup_cfg_filename, 'setup.cfg')
        os.remove('pyproject.toml')

    def test_setup_cfg_format_with_invalid_toml(self):
        if os.path.exists('setup.cfg'):
            os.remove('setup.cfg')
        with open('pyproject.toml', 'w') as f:
            f.write('invalid_toml')
        version = Version()
        self.assertEqual(version.setup_cfg_format, 'setupcfg')
        os.remove('pyproject.toml')

    def test_setup_cfg_format_with_no_files(self):
        if os.path.exists('setup.cfg'):
            os.remove('setup.cfg')
        if os.path.exists('pyproject.toml'):
            os.remove('pyproject.toml')
        version = Version()
        self.assertEqual(version.setup_cfg_format, 'setupcfg')


if __name__ == '__main__':
    unittest.main()
