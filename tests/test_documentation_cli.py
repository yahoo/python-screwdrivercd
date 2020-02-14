# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import unittest
import sys
import tempfile
from screwdrivercd.documentation import cli


class CliTestCase(unittest.TestCase):
    used_env_vars = ['DOCUMENTATION_DEBUG', 'DOCUMENTATION_FORMATS', 'DOCUMENTATION_PUBLISH']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._argv = sys.argv
        self._cwd = os.getcwd()

    def setUp(self):
        self.clear_used_env_keys()

    def tearDown(self):
        sys.argv = self._argv
        os.chdir(self._cwd)
        self.clear_used_env_keys()

    def clear_used_env_keys(self):
        for varname in self.used_env_vars:
            if varname in os.environ.keys():
                del os.environ[varname]

    def test__default__base(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'base'
        sys.argv = ['sdv4_documentation']
        cli.main()

    def test__build__mkdocs__none(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            cli.main()

    def test__build__mkdocs(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n')
            cli.main()

    def test__build__mkdocs_venv(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs_venv'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n')
            result = cli.main()
        self.assertEqual(result, 0)

    def test__build__mkdocs_venv__requirements_missing__fail(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs_venv'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\nmarkdown_extensions:\n    - pymdownx.arithmatex\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n')

            with open('documentation_mkdocs_requirements.txt', 'w') as fh:
                fh.write('mkdocs\n')

            result = cli.main()
        self.assertNotEqual(result, 0)

    def test__build__mkdocs_venv__requirements_present(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs_venv'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\nmarkdown_extensions:\n    - pymdownx.arithmatex\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n')

            with open('documentation_mkdocs_requirements.txt', 'w') as fh:
                fh.write('mkdocs\npymdown-extensions\n')

            result = cli.main()
        self.assertEqual(result, 0)


    def test__build__mkdocs__docsdir(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('docs/mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n')
            cli.main()

    def test__build__mkdocs__fail(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\nstrict: true\nnav:\n    - foo: bar.md\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n[bad_link](bar.md)\n')
            result = cli.main()
            self.assertNotEqual(result, 0)

    def test__build__sphinx__none(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'sphinx'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            cli.main()

    def test__build__sphinx(self):
        os.environ['DOCUMENTATION_DEBUG'] = 'True'
        os.environ['DOCUMENTATION_FORMATS'] = 'sphinx'
        os.environ['DOCUMENTATION_PUBLISH'] = 'False'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('doc/source')
            with open('doc/source/conf.py', 'w') as fh:
                fh.write("""# -*- coding: utf-8 -*-
import os
extensions = []
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'foo'
copyright = ''
version = '0.0.0'
release = version
""")
            with open('doc/source/index.rst', 'w') as fh:
                fh.write('''Title\n-----\n\n''')

            cli.main()

    def test__publish__mkdocs__fail(self):
        os.environ['DOCUMENTATION_FORMATS'] = 'mkdocs'
        os.environ['DOCUMENTATION_PUBLISH'] = 'True'
        sys.argv = ['sdv4_documentation']
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.makedirs('docs')
            with open('mkdocs.yml', 'w') as fh:
                fh.write('site_name: test\nstrict: true\nnav:\n    - foo: bar.md\n')

            with open('docs/index.md', 'w') as fh:
                fh.write('# Title\n[bad_link](bar.md)\n')
            result = cli.main()
            self.assertNotEqual(result, 0)