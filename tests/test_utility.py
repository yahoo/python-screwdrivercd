# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import tempfile
import unittest

from screwdrivercd.utility import create_artifact_directories, env_bool, env_int, flush_terminals
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory, revert_file, working_dir


class TestPlatformTestTox(unittest.TestCase):

    def test_working_dir(self):
        """
        Verify the workingdir context manager switches to the directory
        and switches back correctly.
        :return:
        """

        cwd = os.getcwd()
        tempdir = tempfile.mkdtemp()

        # Change into the temp directory and get the cwd value, we can't use
        # the path for tempdir because the values could be different if
        # there are symlinks in the path.

        os.chdir(tempdir)
        expected_result = os.getcwd()
        os.chdir(cwd)

        with working_dir(expected_result):
            self.assertEqual(os.getcwd(), expected_result)
        self.assertEqual(os.getcwd(), cwd)
        os.removedirs(tempdir)

    def test_working_dir_nested(self):
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = os.getcwd()

            # Change into the tempdir and use getcwd() so that our asserts
            # work properly when the temp directory has a symlink.
            os.chdir(tempdir)
            real_tempdir = os.getcwd()

            dir1 = os.path.join(os.getcwd(), '1')
            dir2 = os.path.join(os.getcwd(), '2')
            os.mkdir(dir1)
            os.mkdir(dir2)
            with working_dir(dir1):
                self.assertEqual(dir1, os.getcwd())
                with working_dir(dir2):
                    self.assertEqual(dir2, os.getcwd())
                self.assertEqual(dir1, os.getcwd())
            self.assertEqual(real_tempdir, os.getcwd())
            os.chdir(cwd)

    def test_revert_file__exists(self):
        with InTemporaryDirectory() as tempdir:
            tfile = os.path.join(tempdir, 'junk')
            with open(tfile, 'w') as fh:
                fh.write('Junk file\n')
            with revert_file(tfile):
                with open(tfile, 'w') as fh:
                    fh.write('Different\n')
                self.assertIn('Different', open(tfile).read())
            self.assertIn('Junk file', open(tfile).read())

    def test_revert_file__missing(self):
        with InTemporaryDirectory() as tempdir:
            tfile = os.path.join(tempdir, 'junk')
            with revert_file(tfile):
                with open(tfile, 'w') as fh:
                    fh.write('Different\n')
                self.assertIn('Different', open(tfile).read())
            self.assertFalse(os.path.exists(tfile))

    def test__InTemporaryDirectory(self):
        cwd = os.getcwd()
        with InTemporaryDirectory() as tempdir:
            self.assertNotEqual(cwd, tempdir)
            self.assertTrue(os.path.isdir(tempdir))
        self.assertFalse(os.path.exists(tempdir))
        self.assertEqual(cwd, os.getcwd())

    def test__flush_terminals(self):
        flush_terminals()
