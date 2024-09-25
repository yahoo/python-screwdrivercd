# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import base64
import os
import stat
import unittest

from screwdrivercd.changelog.generate import changelog_contents, create_first_commit_tag_if_missing, git_tag_dates, write_changelog
from screwdrivercd.changelog.generate import main as changelog_generate_main
from . import ScrewdriverTestCase


working_config = {
    'setup.py': b"""
from setuptools import setup
setup()
""",
    'setup.cfg': b"""
[metadata]
name=mypyvalidator
version=0.0.0

[options]
packages =
    mypyvalidator

package_dir =
    =src
""",
    'src/mypyvalidator/__init__.py': b"""a: int = 1\n"""
}


class ScrewdriverChangelogTestCase(ScrewdriverTestCase):

    def create_example_repo(self):
        print(os.getcwd())

        os.system('git init')
        os.system('git config user.email "foo@bar.com"')
        os.system('git config user.name "foo the bar"')

        self.write_config_files(working_config)
        self.write_config_files({'changelog.d/1.feature.md': b'Initial commit\n'})
        os.system('git add changelog.d/1.feature.md')
        os.system('git commit -a -m "inital commit"')

        self.write_config_files({'changelog.d/2.feature.md': b'Added another new feature\n'})
        os.system('git add changelog.d/2.feature.md')
        os.system('git commit -a -m "second commit"')
        os.system('git tag -a -m "new tag" v0.0.1')

        self.write_config_files({'changelog.d/3.feature.md': b'Added a second new feature\n'})
        os.system('git add changelog.d/3.feature.md')
        os.system('git commit -a -m "third commit"')
        os.system('git tag -a -m "new tag" v0.1.0')

        self.write_config_files({'changelog.d/4.bugfix.md': b'Fixed the second new feature\n'})
        os.system('git add changelog.d/4.bugfix.md')
        os.system('git commit -a -m "forth commit"')
        os.system('git tag -a -m "new tag" v0.1.1')

    def test__changelog_generate_main(self):
        self.create_example_repo()

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator first_commit (', changelog_contents)
        self.assertNotIn('# mypyvalidator new (', changelog_contents)
        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.1 (', changelog_contents)

    def test__changelog_generate_header(self):
        self.create_example_repo()
        self.write_config_files({'changelog.d/HEADER.md': b'# Changelog header\n'})

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator first_commit (', changelog_contents)
        self.assertNotIn('# mypyvalidator new (', changelog_contents)
        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.1 (', changelog_contents)
        self.assertIn('# Changelog header', changelog_contents)

    def test__changelog_generate_footer(self):
        self.create_example_repo()
        self.write_config_files({'changelog.d/FOOTER.md': b'# Changelog footer\n'})

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator first_commit (', changelog_contents)
        self.assertNotIn('# mypyvalidator new (', changelog_contents)
        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.1 (', changelog_contents)
        self.assertIn('# Changelog footer', changelog_contents)

    def test__changelog_generate_main__releases_all(self):
        os.environ['CHANGELOG_RELEASES'] = 'all'
        self.create_example_repo()

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator first_commit (', changelog_contents)
        self.assertNotIn('# mypyvalidator new (', changelog_contents)
        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.1 (', changelog_contents)

    def test__changelog_generate_main__nofilter_nonversons(self):
        os.environ['CHANGELOG_ONLY_VERSION_TAGS'] = 'False'

        self.create_example_repo()

        self.write_config_files({'changelog.d/6.bugfix.md': b'Make sure version filter can be turned off\n'})
        os.system('git add changelog.d/6.bugfix.md')
        os.system('git commit -a -m "sixth commit"')
        os.system('git tag -a -m "latest tag" latest')

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        os.system('git log --date-order --tags --simplify-by-decoration --pretty=format:"%ct|%D"')
        print(changelog_contents)

        self.assertNotIn('# mypyvalidator first_commit (', changelog_contents)
        self.assertIn('# mypyvalidator latest (', changelog_contents)
        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.1 (', changelog_contents)

    def test_generate_main__single_version(self):
        os.environ['CHANGELOG_RELEASES'] = 'v0.1.0'
        self.create_example_repo()

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertNotIn('# mypyvalidator v0.1.1 (', changelog_contents)

    def test_generate_main__selected_versions(self):
        os.environ['CHANGELOG_RELEASES'] = 'v0.0.1, v0.1.0'
        self.create_example_repo()

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertNotIn('# mypyvalidator v0.1.1 (', changelog_contents)

    def test_generate_main__only_stable_true(self):
        os.environ['CHANGELOG_ONLY_STABLE_RELEASES'] = 'True'
        self.create_example_repo()
        self.write_config_files({'changelog.d/10.feature.md': b'Pre-release commit\n'})
        os.system('git add changelog.d/10.feature.md')
        os.system('git commit -a -m "inital commit"')
        os.system('git tag -a -m "pre release" v0.1.10a1')

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertNotIn('# mypyvalidator v0.1.10a1 (', changelog_contents)

    def test_changelog_contents_with_header_and_footer(self):
        header_content = b"# This is the header"
        footer_content = b"# This is the footer"
        self.create_example_repo()
        self.write_config_files({'changelog.d/HEADER.md': header_content, 'changelog.d/FOOTER.md': footer_content})
        os.system('git add changelog.d/HEADER.md')
        os.system('git add changelog.d/FOOTER.md')
        os.system('git commit -a -m "inital commit"')
        os.system('git tag -a -m "pre release" v0.2.10')

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertIn("This is the header", changelog_contents)
        self.assertIn("This is the footer", changelog_contents)

    def test_generate_main__only_stable_false(self):
        os.environ['CHANGELOG_ONLY_STABLE_RELEASES'] = 'False'
        self.create_example_repo()
        self.write_config_files({'changelog.d/10.feature.md': b'Pre-release commit\n'})
        os.system('git add changelog.d/10.feature.md')
        os.system('git commit -a -m "inital commit"')
        os.system('git tag -a -m "pre release" v0.1.10a1')

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertIn('# mypyvalidator v0.0.1 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.0 (', changelog_contents)
        self.assertIn('# mypyvalidator v0.1.10a1 (', changelog_contents)

    def test_create_first_commit_tag_if_missing__missing(self):
        self.create_example_repo()

        before = git_tag_dates()
        self.assertNotIn('first_commit', before.keys())

        create_first_commit_tag_if_missing()

        after = git_tag_dates()
        self.assertIn('first_commit', after.keys())

    def test_create_first_commit_tag_if_missing__present(self):
        self.create_example_repo()

        create_first_commit_tag_if_missing()

        before = git_tag_dates()
        self.assertIn('first_commit', before.keys())

        create_first_commit_tag_if_missing()

        after = git_tag_dates()
        self.assertIn('first_commit', after.keys())

    def test_generate_main__invalid_type(self):
        self.create_example_repo()
        self.write_config_files({'changelog.d/5.moose.md': b'Bad changelog entry\n'})
        os.system('git add changelog.d/5.moose.md')
        os.system('git commit -a -m "fifth commit"')
        os.system('git tag v0.2.0')

        changelog_generate_main()

        self.assertTrue(os.path.exists('artifacts/reports/changelog/changelog.md'))
        with open('artifacts/reports/changelog/changelog.md') as fh:
            changelog_contents = fh.read()

        print(changelog_contents)

        self.assertNotIn('# mypyvalidator v0.2.0 (', changelog_contents)

    def test__create_first_commit_tag_if_missing__exists(self):
        self.create_example_repo()
        create_first_commit_tag_if_missing()
        create_first_commit_tag_if_missing()
