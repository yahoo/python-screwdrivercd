# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import copy
import os
import sys
import unittest

from json import dumps

from screwdrivercd.packaging.build_python import build_sdist_package, build_wheel_packages
from screwdrivercd.utility.environment import standard_directories
from screwdrivercd.utility.output import header
from screwdrivercd.utility.tox import run_tox
from screwdrivercd.validation.validate_dependencies import validate_with_safety
from screwdrivercd.validation.validate_package_quality import validate_package_quality
from screwdrivercd.validation.validate_style import main as style_main
from screwdrivercd.validation.validate_style import validate_codestyle
from screwdrivercd.validation.validate_type import main as type_main
from screwdrivercd.validation.validate_type import validate_type
from screwdrivercd.validation.validate_unittest import main as unittest_main

from . import ScrewdriverTestCase


class ScrewdriverValidatorTestCase(ScrewdriverTestCase):
    """
    Base class to test validation wrappers
    """


# Simple working package tree
working_config = {
    'setup.py': b"""
from setuptools import setup
setup()
""",
    'setup.cfg': b"""
[metadata]
author = Verizon Media Python Platform Team
author_email = python@verizonmedia.com
name=mypyvalidator
url=https://foo.bar.com/
version=0.0.0

[options]
packages =
    mypyvalidator

package_dir =
    =src
""",
    'src/mypyvalidator/__init__.py': b"""a: int = 1\n""",
    'tests/test.py': b"""from unittest import TestCase

class DummyTestCase(TestCase):
    def test_dummy(self):
        import mypyvalidator
        self.assertEqual(mypyvalidator.a, 1)
""",
    'tox.ini': b"""
[config]
package_dir = src/mypyvalidator
package_name = mypyvalidator

[tox]
envlist = py39,py310,py311
skip_missing_interpreters = true

[testenv]
changedir = {toxinidir}
commands = 
     python -c "import sys;print(sys.version_info)"
"""
}

# No source package tree
working_config_nosrc = copy.deepcopy(working_config)
working_config_nosrc['mypyvalidator/__init__.py'] = working_config_nosrc['src/mypyvalidator/__init__.py']
del working_config_nosrc['src/mypyvalidator/__init__.py']
working_config_nosrc['setup.cfg'] = b"""
[metadata]
name=mypyvalidator
version=0.0.0

[options]
packages =
    mypyvalidator
"""

# src dir has different case than package name
working_config_case_different = copy.deepcopy(working_config)
working_config_case_different['src/MyPyvalidator/__init__.py'] = working_config['src/mypyvalidator/__init__.py']
del working_config_case_different['src/mypyvalidator/__init__.py']
working_config_case_different['setup.cfg'].replace(b'\n    mypyvalidator', b'\n    MyPyvalidator')

# No source dir different case
working_config_case_different_nosrc = copy.deepcopy(working_config_case_different)
working_config_case_different_nosrc['MyPyvalidator/__init__.py'] = working_config_case_different_nosrc['src/MyPyvalidator/__init__.py']
del working_config_case_different_nosrc['src/MyPyvalidator/__init__.py']

# Invalid package tree
invalid_type_config = copy.deepcopy(working_config)
invalid_type_config['src/mypyvalidator/__init__.py'] = b"""a: int='1'"""

# Insecure dependency
insecure_dep_config = copy.deepcopy(working_config)
insecure_dep_config['setup.cfg'] = b"""
[metadata]
name=mypyvalidator
version=0.0.0

[options]
install_requires =
    insecure-package
    
packages =
    mypyvalidator

package_dir =
    =src
"""

# tox fail
tox_fail_config = copy.deepcopy(working_config)
tox_fail_config['tox.ini'] = b"""
[config]
package_dir = src/mypyvalidator
package_name = mypyvalidator

[tox]
envlist = py39,py310,py311
skip_missing_interpreters = true

[testenv]
changedir = {toxinidir}
commands = 
	python -c "import sys;sys.exit(1)"
"""

invalid_style_config = copy.deepcopy(working_config)
invalid_style_config['src/mypyvalidator/__init__.py'] = b"""a: int =1\n"""

class DepValidatorTestcase(ScrewdriverTestCase):
    validator_name = 'type_validation'

    @unittest.skip("No longer works, safety is no longer used for validation")
    def test__secure_deps(self):
        self.write_config_files(working_config)
        result = validate_with_safety()
        self.assertEqual(result, 0)

    @unittest.skip("No longer works, safety is no longer used for validation")
    def test__insecure_deps(self):
        self.write_config_files(insecure_dep_config)
        artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
        report_dir = os.path.join(artifacts_dir, 'reports/dependency_validation')
        json_report_filename = os.path.join(report_dir, 'safetydb.json')
        result = validate_with_safety()
        self.assertGreater(result, 0)
        os.system(f'ls -lh {report_dir}')
        self.assertTrue(os.path.exists(json_report_filename))


class StyleValidator(ScrewdriverTestCase):
    validator_name = 'style_validation'

    def test__style__pass__srcdir_main(self):
        os.environ['PACKAGE_DIR'] = 'src'
        self.write_config_files(working_config)
        result = style_main()
        self.assertEqual(result, 0)

    def test__style__pass__srcdir(self):
        os.environ['PACKAGE_DIR'] = 'src'
        self.write_config_files(working_config)
        result = validate_codestyle()
        self.assertEqual(result, 0)

    def test__style__pass__srcdir__args(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['CODESTYLE_ARGS'] = '--show-source'
        self.write_config_files(working_config)
        result = validate_codestyle()
        self.assertEqual(result, 0)

    def test__style__fail__srcdir(self):
        os.environ['PACKAGE_DIR'] = 'src'
        self.write_config_files(invalid_style_config)
        result = validate_codestyle()
        self.assertGreater(result, 0)

    def test__style__pass__nosrc(self):
        self.write_config_files(working_config_nosrc)
        result = validate_codestyle()
        self.assertEqual(result, 0)

    def test_style__pass__srcdir_wrong_case(self):
        os.environ['PACKAGE_DIR'] = 'src'
        self.write_config_files(working_config_case_different)
        os.system('ls -lR')
        result = validate_codestyle()
        self.assertEqual(result, 0)

    def test_style__pass__srcdir_wrong_case__missing(self):
        os.environ['PACKAGE_DIR'] = 'srcz'
        self.write_config_files(working_config_case_different)
        os.system('ls -lR')
        result = validate_codestyle()
        self.assertNotEqual(result, 0)

    def test_style__pass__nosrcdir_wrong_case(self):
        self.write_config_files(working_config_case_different_nosrc)
        os.system('ls -lR')
        os.system('cat setup.cfg')
        result = validate_codestyle()
        self.assertEqual(result, 1)


class TypeValidatorTestcase(ScrewdriverTestCase):
    validator_name = 'type_validation'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.environ_keys.add('MYPY_ARGS')
        self.environ_keys.add('TYPE_CHECK_ENFORCING')
        self.environ_keys.add('TYPE_CHECK_REPORT_FORMAT')

    def test__main__valid(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        self.write_config_files(working_config)
        result = type_main()
        self.assertEqual(result, 0)

    def test__main__valid_nosrc(self):
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        self.write_config_files(working_config_nosrc)
        result = type_main()
        self.assertEqual(result, 0)

    def test__mypy__valid(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        self.write_config_files(working_config)
        result = validate_type()
        self.assertEqual(result, 0)

    def test__mypy__valid__nopackage_dir__env(self):
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        self.write_config_files(working_config)
        result = validate_type()
        self.assertEqual(result, 0)

    def test__mypy__valid__mypy_args(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        os.environ['MYPY_ARGS'] = '--show-error-context'

        self.write_config_files(working_config)
        result = validate_type()
        self.assertEqual(result, 0)

    def test__mypy__invalid_not_enforcing(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'False'

        self.write_config_files(invalid_type_config)
        result = validate_type()
        self.assertEqual(result, 0)

    def test__mypy__invalid_enforcing(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'

        self.write_config_files(invalid_type_config)
        result = validate_type()
        self.assertGreater(result, 0)
        self.assertTrue(os.path.exists(f'{self.artifacts_dir}/reports/{self.validator_name}/index.txt'))

    def test__mypy__invalid_enforcing_lxml_report(self):
        os.environ['PACKAGE_DIR'] = 'src'
        os.environ['TYPE_CHECK_ENFORCING'] = 'True'
        os.environ['TYPE_CHECK_REPORT_FORMAT'] = 'junit-xml'
        print(dumps(dict(os.environ), indent=4, sort_keys=True))
        self.write_config_files(invalid_type_config)
        result = validate_type()
        self.assertGreater(result, 0)
        self.assertTrue(os.path.exists(f'{self.artifacts_dir}/reports/{self.validator_name}/mypy.xml'))


class PackageQualityValidatorTestCase(ScrewdriverTestCase):
    validator_name = 'package_quality_validator'

    def test__quality__no_package_directory(self):
        package_dir = standard_directories('package_quality_validation')['packages']
        if os.path.exists(package_dir):
            os.rename(package_dir, package_dir + '.disabled')
        result = validate_package_quality()
        self.assertEqual(result, 0)

    def test__quality__no_package_default_fail(self):
        result = validate_package_quality()
        self.assertEqual(result, 0)

    def test__quality__no_package_fail(self):
        os.environ['VALIDATE_PACKAGE_QUALITY_FAIL_MISSING'] = 'True'
        result = validate_package_quality()
        self.assertEqual(result, 1)

    def test__quality__no_package_nofail(self):
        os.environ['VALIDATE_PACKAGE_QUALITY_FAIL_MISSING'] = 'False'
        result = validate_package_quality()
        self.assertEqual(result, 0)

    def test__quality__fail(self):
        os.environ['PYROMA_MIN_SCORE'] = '9'
        self.write_config_files(working_config)
        build_sdist_package()
        result = validate_package_quality()
        self.assertNotEqual(result, 0)

    def test__quality__pass__0(self):
        os.environ['PYROMA_MIN_SCORE'] = '0'
        self.write_config_files(working_config)
        build_sdist_package()
        result = validate_package_quality()
        self.assertEqual(result, 0)

    def test__quality__skip_wheel_pass__0(self):
        os.environ['PYROMA_MIN_SCORE'] = '0'
        self.write_config_files(working_config)
        build_sdist_package()
        build_wheel_packages()
        result = validate_package_quality()
        self.assertEqual(result, 0)


class UnitTestValidatorTestCase(ScrewdriverTestCase):
    validator_name = 'unittest'

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__default(self):
        self.write_config_files(working_config)
        result = unittest_main()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__fail(self):
        self.write_config_files(tox_fail_config)
        result = unittest_main()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertNotEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__no_artifacts_dir(self):
        del os.environ['SD_ARTIFACTS_DIR']
        self.write_config_files(working_config)
        result = unittest_main()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__tox_args(self):
        os.environ['TOX_ARGS'] = '-v'
        self.write_config_files(working_config)
        result = unittest_main()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__tox_args_arg(self):
        self.write_config_files(working_config)
        result = run_tox()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__tox_envlist(self):
        os.environ['TOX_ENVLIST'] = f'py{sys.version_info.major}{sys.version_info.minor}'
        self.write_config_files(working_config)
        result = unittest_main()
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)

    @unittest.skip("No longer works with newer tox releases")
    def test__unittest__tox_envlist_arg(self):
        self.write_config_files(working_config)
        result = run_tox(tox_envlist=f'py{sys.version_info.major}{sys.version_info.minor}')
        for dirpath, dirs, files in os.walk('.tox'):
            for fname in files:
                if fname.endswith('.log'):
                    filename = os.path.join(dirpath, fname)
                    header(filename)
                    with open(filename) as fh:
                        print(fh.read() + os.linesep)
        self.assertEqual(result, 0)
