# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import os
from screwdrivercd.packaging.build_python import main as build_python_main
from screwdrivercd.packaging.publish_python import main as publish_python_main, package_exists, poll_until_available
from screwdrivercd.utility.environment import standard_directories
from vcr_unittest import VCRTestCase

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


class ScrewdriverPackagingTestCase(ScrewdriverTestCase):

    def test__packaging__main__sdist(self):
        os.environ['PACKAGE_TYPES'] = 'sdist'
        self.write_config_files(working_config)
        build_python_main()

        print(os.listdir('artifacts/packages'))
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

    def test__packaging__main__wheel(self):
        os.environ['PACKAGE_TYPES'] = 'wheel'
        self.write_config_files(working_config)
        build_python_main()

        print(os.listdir('artifacts/packages'))
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0-py3-none-any.whl'))


class ScrewdriverPackagingPublishTestCase(ScrewdriverTestCase):
    def moc_twine_command(self, rc=0, stdout='stdout', stderr='stderr'):
        twine_command_filename = os.path.join(self.tempdir.name, 'twine')
        with open(twine_command_filename, 'w') as fh:
            os.fchmod(fh.fileno(), 0o0755)
            fh.write(f'#!/bin/bash\nprintenv\n')
            if stdout:
                fh.write(f'\ncat << EOF\n{stdout}\nEOF\n')
            if stderr:
                fh.write(f'\ncat << EOF >&2\n{stderr}\nEOF\n')
            fh.write(f'exit {rc}\n')
        return twine_command_filename

    def test__publish__no_package_dir(self):
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        package_dir = standard_directories('publish_python')['packages']
        if os.path.exists(package_dir):
            print(package_dir)
            os.rename(package_dir, package_dir + '.disabled')
        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))
        self.assertEqual(rc, 0)

    def test__publish__disabled(self):
        os.environ['PUBLISH_PYTHON'] = 'False'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        package_dir = standard_directories('publish_python')['packages']
        os.makedirs(package_dir, exist_ok=True)
        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))
        self.assertEqual(rc, 0)

    def test__publish__sdist__fails_user_secret(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__fails_user_password(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PYPI_USER'] = 'foo'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__fails_user_twine(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PYPI_USER'] = 'foo'
        os.environ['PYPI_PASSWORD'] = 'bar'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__pass__no_file_missing_cred(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'False'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 0)

    def test__publish__sdist(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PYPI_USER'] = 'foo'
        os.environ['PYPI_PASSWORD'] = 'bar'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=0))

        self.assertEqual(rc, 0)

    def test__publish__sdist__fail(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PYPI_USER'] = 'foo'
        os.environ['PYPI_PASSWORD'] = 'bar'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__test_pypi(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['TEST_PYPI_USER'] = 'foo'
        os.environ['TEST_PYPI_PASSWORD'] = 'bar'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        os.environ['TWINE_REPOSITORY_URL'] = 'https://test.pypi.org/legacy/'
        os.environ['PUBLISH_PYTHON_TIMEOUT'] = "0"
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=0))

        self.assertEqual(rc, 0)


class ScrewdriverPackagingPollerTestCase(VCRTestCase):
    def _get_vcr_kwargs(self):
        """
        Set the VCR settings
        """
        return dict(
            record_mode='new_episodes',
            decode_compressed_response=True,
        )

    def test__package_exists__true(self):
        result = package_exists('setuptools', 'setuptools-68.0.0.tar.gz')
        self.assertTrue(result)

    def test__package_exists__false(self):
        result = package_exists('foozle', 'foozle-9999.9999.32.zip')
        self.assertFalse(result)

    def test__poll_until_available__ok(self):
        result = poll_until_available('serviceping', {'serviceping-19.5.78.tar.gz', 'serviceping-19.5.121522-py3-none-any.whl'}, timeout=30)
        self.assertIsInstance(result, set)
        self.assertFalse(result)

    def test__poll_until_available__fail(self):
        result = poll_until_available('serviceping', {'serviceping-19.5.78.tar.gz', 'serviceping-19.9999.121522-py3-none-any.whl'}, timeout=5)
        self.assertIsInstance(result, set)
        self.assertEqual(result, {'serviceping-19.9999.121522-py3-none-any.whl'})
