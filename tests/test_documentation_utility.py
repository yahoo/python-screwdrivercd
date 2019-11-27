# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import pathlib
import tempfile
import unittest

from screwdrivercd.documentation.utility import clean_directory, copy_contents
from screwdrivercd.utility import env_bool
from . import ScrewdriverTestCase

class UtilityTestCase(ScrewdriverTestCase):

    def setUp(self):
        super().setUp()
        self.testfiles = [
            f'{self.tempdir.name}/testfile',
            f'{self.tempdir.name}/.testfile',
        ]

    def _create_testfiles(self):
        for filename in self.testfiles:
            pathlib.Path(filename).touch()
            self.assertTrue(os.path.exists(filename))

    def test_clean_directory(self):
        self._create_testfiles()
        clean_directory(self.tempdir.name)
        self.assertFalse(os.path.exists(f'{self.tempdir.name}/testfile'))
        self.assertTrue(os.path.exists(f'{self.tempdir.name}/.testfile'))

    def test_copy_contents(self):
        os.makedirs('source')
        os.makedirs('dest')
        pathlib.Path(f'source/testfile').touch()
        pathlib.Path(f'source/.testfile').touch()

        self.assertFalse(os.path.exists(f'dest/testfile'))
        self.assertFalse(os.path.exists(f'dest/.testfile'))
        copy_contents('source', 'dest')
        self.assertTrue(os.path.exists(f'dest/testfile'))
        self.assertTrue(os.path.exists(f'dest/.testfile'))

    def test_copy_contents__skip_dotfiles(self):
        os.makedirs('source')
        os.makedirs('dest')
        pathlib.Path(f'source/testfile').touch()
        pathlib.Path(f'source/.testfile').touch()

        self.assertFalse(os.path.exists(f'dest/testfile'))
        self.assertFalse(os.path.exists(f'dest/.testfile'))
        copy_contents('source', 'dest', skip_dotfiles=True)
        self.assertTrue(os.path.exists(f'dest/testfile'))
        self.assertFalse(os.path.exists(f'dest/.testfile'))
