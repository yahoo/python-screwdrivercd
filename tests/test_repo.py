# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import base64
import os

from screwdrivercd.changelog.generate import changelog_contents, create_first_commit_tag_if_missing, git_tag_dates, write_changelog
from screwdrivercd.repo.release import main as release_main
from screwdrivercd.repo.release import create_release_tag, push_release_tag
from screwdrivercd.utility.environment import env_int, env_bool, interpreter_bin_command, standard_directories


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


class TestPlatformRepoRelease(ScrewdriverTestCase):

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

    def moc_command(self, command='git', rc=0, stdout='stdout', stderr='stderr', delay=0):
        command_filename = os.path.join(self.tempdir.name, command)
        with open(command_filename, 'w') as fh:
            os.fchmod(fh.fileno(), 0o0755)
            fh.write(f'#!/bin/bash\n')
            if stdout:
                fh.write(f'\ncat << EOF\n{stdout}\nEOF\n')
            if stderr:
                fh.write(f'\ncat << EOF >&2\n{stderr}\nEOF\n')
            if delay:
                fh.write(f'\nsleep {delay}\n')
            fh.write(f'exit {rc}\n')
        return command_filename

    def test__release__main__publish_disabled(self):
        os.environ['PUBLISH'] = 'False'
        result = release_main()
        self.assertEqual(result, 0)

    def test__release__main__package_tag__disabled(self):
        os.environ['PUBLISH'] = 'True'
        os.environ['PACKAGE_TAG'] = 'False'
        result = release_main()
        self.assertEqual(result, 0)

    def test__release__main__git_deploy_key__missing(self):
        os.environ['PUBLISH'] = 'True'
        os.environ['PACKAGE_TAG'] = 'True'
        result = release_main()
        self.assertEqual(result, 0)

    def test__release__create_tag(self):
        self.create_example_repo()
        create_release_tag(version='999.999.999')
        result = git_tag_dates()
        self.assertIn('v999.999.999', result.keys())

    def test__release__create_tag__message(self):
        self.create_example_repo()
        create_release_tag(version='999.999.999', message='test message')
        result = git_tag_dates()
        self.assertIn('v999.999.999', result.keys())

    def test__release__create_tag__git_error(self):
        self.create_example_repo()
        create_release_tag(version='999.999.999', git_command=self.moc_command(command='git', rc=999))

    def test__release_push_tag(self):
        self.create_example_repo()
        push_release_tag(git_command=self.moc_command(command='git', rc=0))

    def test__release_push_tag__cmd_missing(self):
        self.create_example_repo()
        push_release_tag(git_command=self.moc_command(command='gitbad', rc=1))

    def test__release_push_tag__fail(self):
        self.create_example_repo()
        push_release_tag(git_command=self.moc_command(command='git', rc=1))

    def test__release_push_tag__timeout(self):
        self.create_example_repo()
        push_release_tag(git_command=self.moc_command(command='git', rc=0, delay=61), timeout=1)

    def test__main(self):
        test_key = b'-----BEGIN RSA PRIVATE KEY-----\nno real key here\n-----END RSA PRIVATE KEY-----\n'
        os.environ['GIT_DEPLOY_KEY'] = base64.b64encode(test_key).decode(errors='ignore')
        self.create_example_repo()
        release_main(meta_command=self.moc_command(command='meta', stdout='999.999.999'))
        result = git_tag_dates()
        self.assertIn('v999.999.999', result.keys())

    def test__main__no_version(self):
        test_key = b'-----BEGIN RSA PRIVATE KEY-----\nno real key here\n-----END RSA PRIVATE KEY-----\n'
        os.environ['GIT_DEPLOY_KEY'] = base64.b64encode(test_key).decode(errors='ignore')
        self.create_example_repo()
        release_main(meta_command=self.moc_command(command='meta', stdout='null'))
