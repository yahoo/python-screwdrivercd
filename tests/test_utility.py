# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import subprocess
import sys
import tempfile

from screwdrivercd.screwdriver.environment import update_job_status
from screwdrivercd.utility.contextmanagers import InTemporaryDirectory, revert_file, working_dir
from screwdrivercd.utility.environment import env_bool, env_int, flush_terminals, interpreter_bin_command
from screwdrivercd.utility.package import run_setup_command, setup_query, PackageMetadata
from screwdrivercd.utility.screwdriver import create_artifact_directory
from screwdrivercd.utility.run import run_and_log_output

from . import ScrewdriverTestCase


class TestPlatformTestTox(ScrewdriverTestCase):

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

    def test__interpreter_bin_command__default(self):
        result = interpreter_bin_command()
        self.assertIsInstance(result, (str))
        self.assertTrue(result.endswith('/python'))
        self.assertTrue(os.path.exists(result))

    def test__interpreter_bin_command__command_exists(self):
        result = interpreter_bin_command('screwdrivercd_version')
        self.assertIsInstance(result, (str))
        self.assertTrue(result.endswith('/screwdrivercd_version'))
        self.assertTrue(os.path.exists(result))

    def test__interpreter_bin_command__command_missing__default(self):
        result = interpreter_bin_command('screwdrivercd_test__interpreter_bin_command__command_missing')
        self.assertIsInstance(result, (str))
        self.assertEqual(result, 'screwdrivercd_test__interpreter_bin_command__command_missing')

    def test__interpreter_bin_command__command_missing__fallback_path__false(self):
        result = interpreter_bin_command('screwdrivercd_test__interpreter_bin_command__command_missing', fallback_path=False)
        self.assertIsInstance(result, (str))
        self.assertFalse(result)  # Empty string evaluates as False

    def test__environement__env_int(self):
        os.environ['test__environement__env_int'] = '1'
        result = env_int('test__environement__env_int')
        del os.environ['test__environement__env_int']
        self.assertEqual(result, 1)

    def test__environement__env_int__default(self):
        result = env_int('test__environement__env_int__default')
        self.assertEqual(result, 0)

    def test_environment_env_bool_default_true(self):
        self.assertTrue(env_bool('TEST_UTILITY_ENV_BOOL', True))

    def test_environment_env_bool_default_false(self):
        self.assertFalse(env_bool('TEST_UTILITY_ENV_BOOL', False))

    def test_environment_env_bool_true(self):
        os.environ['TEST_UTILITY_ENV_BOOL'] = 'True'
        self.assertTrue(env_bool('TEST_UTILITY_ENV_BOOL', False))

    def test_environment_env_bool_false(self):
        os.environ['TEST_UTILITY_ENV_BOOL'] = 'False'
        self.assertFalse(env_bool('TEST_UTILITY_ENV_BOOL', True))

    def test__create_artifact_directory_env(self):
        os.environ['SD_ARTIFACTS_DIR'] = f'{self.tempdir.name}/test_artifacts'
        self.assertFalse(os.path.exists(os.environ['SD_ARTIFACTS_DIR']))
        create_artifact_directory()
        self.assertTrue(os.path.exists(os.environ['SD_ARTIFACTS_DIR']))

    def test__create_artifact_directory_passed(self):
        self.assertFalse(os.path.exists(f'{self.tempdir.name}/test_artifacts'))
        create_artifact_directory(f'{self.tempdir.name}/test_artifacts')
        self.assertTrue(os.path.exists(f'{self.tempdir.name}/test_artifacts'))

    def test__run__run_log_output__success(self):
        with InTemporaryDirectory():
            result = run_and_log_output(['echo', 'hello'], 'echo.log')
            self.assertTrue(os.path.exists('echo.log'))
            with open('echo.log') as fh:
                log_output = fh.read()
            self.assertEqual(log_output, 'hello\n')

    def test__run__run_log_output__fail(self):
        testscript_content = """import sys
print('hello')
sys.exit(1)
"""
        with InTemporaryDirectory():
            with open('testscript.py', 'w') as fh:
                fh.write(testscript_content)
            with self.assertRaises(subprocess.CalledProcessError):
                result = run_and_log_output([sys.executable, 'testscript.py'], 'test.log')
            self.assertTrue(os.path.exists('test.log'))
            with open('test.log') as fh:
                test_output = fh.read()
            self.assertEqual(test_output, 'hello\n')

    def test__setup_query(self):
        with InTemporaryDirectory():
            with open('setup.py', 'w') as setup_py_handle:
                setup_py_handle.write('from setuptools import setup\nsetup(name="foo")\n')
            result = setup_query('--name')
            self.assertEqual(result, 'foo')

    def test__setup_query__cli_args(self):
        with InTemporaryDirectory():
            with open('setup.py', 'w') as setup_py_handle:
                setup_py_handle.write('from setuptools import setup\nsetup(name="foo")\n')
            result = setup_query('--name', cli_args='--verbose')
            self.assertEqual(result, 'foo')

    def test__PackageMetadata__archive(self):
        with InTemporaryDirectory():
            with open('setup.py', 'w') as setup_py_handle:
                setup_py_handle.write('from setuptools import setup\nsetup(name="foo", version="0.0.0")\n')
            setup_query('sdist')
            expected_filename = f'dist/foo-0.0.0.tar.gz'
            self.assertTrue(os.path.exists(expected_filename))
            PackageMetadata(expected_filename)

    def test__PackageMetadata__archive_zip(self):
        with InTemporaryDirectory():
            with open('setup.py', 'w') as setup_py_handle:
                setup_py_handle.write('from setuptools import setup\nsetup(name="foo", version="0.0.0")\n')
            setup_query('sdist', cli_args=['--formats', 'zip'])
            expected_filename = f'dist/foo-0.0.0.zip'
            self.assertTrue(os.path.exists(expected_filename))
            PackageMetadata(expected_filename)

    def test__update_job_status__invalid_status(self):
        with self.assertRaises(KeyError):
            update_job_status('BADDD', message='mojo')
