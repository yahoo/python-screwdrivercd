# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import base64
import os
import stat
import unittest

from screwdrivercd.packaging.build_python import build_sdist_package, build_wheel_packages
from screwdrivercd.packaging.build_python import main as build_python_main
from screwdrivercd.packaging.publish_python import main as publish_python_main

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
    def moc_twine_command(self, rc=0):
        twine_command_filename = os.path.join(self.tempdir.name, 'twine')
        with open(twine_command_filename, 'w') as fh:
            os.fchmod(fh.fileno(), 0o0755)
            fh.write(f'#!/bin/bash\nprintenv\nexit {rc}\n')
        return twine_command_filename

    def test__publish__no_package_dir(self):
        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))
        self.assertEqual(rc, 0)

    def test__publish__sdist__fails_user_secret(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PACKAGE_TYPES'] = 'sdist'
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__fails_user_password(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'True'
        os.environ['PYPI_USER'] = 'foo'
        os.environ['PACKAGE_TYPES'] = 'sdist'
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
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=999))

        self.assertEqual(rc, 1)

    def test__publish__sdist__pass__no_file_missing_cred(self):
        os.environ['PUBLISH_PYTHON_FAIL_MISSING_CRED'] = 'False'
        os.environ['PACKAGE_TYPES'] = 'sdist'
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
        self.write_config_files(working_config)
        build_python_main()
        self.assertTrue(os.path.exists('artifacts/packages/mypyvalidator-0.0.0.tar.gz'))

        rc = publish_python_main(twine_command=self.moc_twine_command(rc=0))

        self.assertEqual(rc, 0)
