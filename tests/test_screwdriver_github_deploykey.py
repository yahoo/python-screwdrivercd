# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import os
import stat
import unittest

from screwdrivercd.screwdriver.github_deploykey import add_github_to_known_hosts, validate_known_good_hosts
from . import ScrewdriverTestCase


class ScrewdriverGithubDeploykeyTestCase(ScrewdriverTestCase):
    environ_keys = {'GIT_KEY', 'SD_BUILD', 'SD_BUILD_ID', 'SD_PULL_REQUEST'}

    def setUp(self):
        super().setUp()
        self.known_hosts_filename = os.path.join(self.tempdir.name, '.ssh/known-hosts')

    @unittest.skipIf(not os.path.exists( '/usr/bin/ssh-keyscan'))
    def test__add_github_to_known_hosts(self):
        result = add_github_to_known_hosts(self.known_hosts_filename)
        self.assertTrue(os.path.exists(self.known_hosts_filename))
        mode = stat.filemode(os.stat(self.known_hosts_filename).st_mode)
        self.assertEqual(mode, '-rw-------')

    def test__validate_known_good_hosts(self):
        add_github_to_known_hosts(self.known_hosts_filename)
        result = validate_known_good_hosts(self.known_hosts_filename)
        self.assertTrue(result)
