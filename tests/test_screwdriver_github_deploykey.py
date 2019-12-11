# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import base64
import os
import stat
import unittest

from screwdrivercd.screwdriver.github_deploykey import add_github_to_known_hosts, git_key_secret, validate_known_good_hosts
from . import ScrewdriverTestCase


class ScrewdriverGithubDeploykeyTestCase(ScrewdriverTestCase):
    environ_keys = {'GIT_DEPLOY_KEY', 'SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'}

    def setUp(self):
        super().setUp()
        self.known_hosts_filename = os.path.join(self.tempdir.name, '.ssh/known-hosts')

    @unittest.skipIf(not os.path.exists( '/usr/bin/ssh-keyscan'), 'The ssh-keyscan command is missing')
    def test__add_github_to_known_hosts(self):
        result = add_github_to_known_hosts(self.known_hosts_filename)
        self.assertTrue(os.path.exists(self.known_hosts_filename))
        mode = stat.filemode(os.stat(self.known_hosts_filename).st_mode)
        self.assertEqual(mode, '-rw-------')

    @unittest.skip
    def test__validate_known_good_hosts(self):
        add_github_to_known_hosts(self.known_hosts_filename)
        result = validate_known_good_hosts(self.known_hosts_filename)
        self.assertTrue(result)

    def test__git_key_secret(self):
        test_key = b'-----BEGIN RSA PRIVATE KEY-----\nno real key here\n-----END RSA PRIVATE KEY-----\n'
        os.environ['GIT_DEPLOY_KEY'] = base64.b64encode(test_key).decode(errors='ignore')
        result = git_key_secret()
        self.assertEqual(result, test_key)

    def test__git_key_secret__nobegin(self):
        test_key = b'no real key here\n-----END RSA PRIVATE KEY-----\n'
        os.environ['GIT_DEPLOY_KEY'] = base64.b64encode(test_key).decode(errors='ignore')
        result = git_key_secret()
        self.assertEqual(result, test_key)

    def test__git_key_secret__noend(self):
        test_key = b'-----BEGIN RSA PRIVATE KEY-----\nno real key here\n'
        os.environ['GIT_DEPLOY_KEY'] = base64.b64encode(test_key).decode(errors='ignore')
        result = git_key_secret()
        self.assertEqual(result, test_key)

    def test__git_key_secret__empty(self):
        result = git_key_secret()
        self.assertEqual(result, b'')
