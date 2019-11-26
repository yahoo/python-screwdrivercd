# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for termsimport copy
import copy
from json import dumps
import os
from . import ScrewdriverTestCase
from screwdrivercd.packaging.build_python import build_sdist_package
from screwdrivercd.validation.validate_dependencies import validate_with_safety
from screwdrivercd.validation.validate_package_quality import validate_package_quality
from screwdrivercd.validation.validate_style import main as style_main
from screwdrivercd.validation.validate_style import validate_codestyle
from screwdrivercd.validation.validate_type import main as type_main
from screwdrivercd.validation.validate_type import validate_type


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

invalid_style_config = copy.deepcopy(working_config)
invalid_style_config['src/mypyvalidator/__init__.py'] = b"""a: int =1\n"""

class DepValidatorTestcase(ScrewdriverTestCase):
    validator_name = 'type_validation'

    def test__secure_deps(self):
        self.write_config_files(working_config)
        result = validate_with_safety()
        self.assertEqual(result, 0)

    def test__insecure_deps(self):
        self.write_config_files(insecure_dep_config)
        artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
        report_dir = os.path.join(artifacts_dir, 'reports/dependency_validation')
        json_report_filename = os.path.join(report_dir, 'safetydb.json')
        result = validate_with_safety()
        self.assertGreater(result, 0)
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

    def test__quality(self):
        self.write_config_files(working_config)
        build_sdist_package()
        result = validate_package_quality()
        self.assertEqual(result, 0)
