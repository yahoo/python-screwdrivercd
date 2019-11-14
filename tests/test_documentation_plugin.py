# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import os
import tempfile
import unittest
from pathlib import Path
import screwdrivercd.documentation.exceptions
import screwdrivercd.documentation.plugin
import screwdrivercd.documentation.mkdocs.plugin
import screwdrivercd.documentation.sphinx.plugin


class PluginsTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._pwd)

    def test__documentation_plugins__present(self):
        names = [_.name for _ in screwdrivercd.documentation.plugin.documentation_plugins()]
        self.assertIn('mkdocs', names)
        self.assertIn('sphinx', names)


class DocumentationPluginTestCase(unittest.TestCase):
    plugin_class = screwdrivercd.documentation.plugin.DocumentationPlugin
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._pwd)

    def _create_test_repo_contents(self):
        pass

    def test_documentation_base_plugin_is_present(self):
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        self.assertFalse(p.documentation_is_present)

    def test_documentation_base__log_message(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            p = self.plugin_class()
            p.build_log_filename = 'foo.log'
            p._log_message('foo', p.build_log_filename)
            self.assertTrue(os.path.exists('foo.log'))
            with open('foo.log') as log:
                self.assertEqual('foo\n', log.read())

    def test_documentation__base__run_command(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            p = self.plugin_class()
            p.build_log_filename = 'foo.log'
            p._run_command(['echo', 'hello'], log_filename=p.build_log_filename)
            self.assertTrue(os.path.exists('foo.log'))
            with open('foo.log') as log:
                self.assertEqual('hello\n', log.read())

    def test_documentation__base__run_command__errror(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            p = self.plugin_class()
            p.build_log_filename = 'foo.log'
            with self.assertRaises(screwdrivercd.documentation.exceptions.DocBuildError):
                p._run_command(['./exit', '1'], log_filename=p.build_log_filename)

    def test__documentation__build(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            self._create_test_repo_contents()
            p = self.plugin_class()
            p.build_documentation()
            self.assertTrue(os.path.exists(f'{p.log_dir}/{p.name}.build.log'))


class SphinxDocumentationPluginTestCase(DocumentationPluginTestCase):
    plugin_class = screwdrivercd.documentation.sphinx.plugin.SphinxDocumentationPlugin

    def _create_test_repo_contents(self):
        os.makedirs('doc/source')

    def test__documentation__build(self):
        pass


class MkdocsDocumentationPluginTestCase(DocumentationPluginTestCase):
    plugin_class = screwdrivercd.documentation.mkdocs.plugin.MkDocsDocumentationPlugin

    def _create_test_repo_contents(self):
        os.makedirs('docs')

    def test__documentation__build(self):
        pass
