import copy
import os
from . import ScrewdriverTestCase
from screwdrivercd.validation.validate_type import main as type_main
from screwdrivercd.validation.validate_type import validate_type


class ScrewdriverValidatorTestCase(ScrewdriverTestCase):
    """
    Base class to test validation wrappers
    """


# Simple working package tree
working_config = {
    'src/setup.py': b"""
from setuptools import setup
setup()
""",
    'src/setup.cfg': b"""
[metadata]
name=mypyvalidator
version=0.0.0
""",
    'src/mypyvalidator/__init__.py': b"""a: int=1"""
}

# Invalid package tree
invalid_type_config = copy.deepcopy(working_config)
invalid_type_config['src/mypyvalidator/__init__.py'] = b"""a: int='1'"""


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
        self.write_config_files(invalid_type_config)
        result = validate_type()
        self.assertGreater(result, 0)
        self.assertTrue(os.path.exists(f'{self.artifacts_dir}/reports/{self.validator_name}/mypy.xml'))
