# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import base64
import os
import stat
import unittest

from screwdrivercd.packaging.build_python import build_sdist_package, build_wheel_packages
from screwdrivercd.packaging.build_python import main as build_python_main
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
