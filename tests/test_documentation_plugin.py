# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
import hashlib
import os
from pathlib import Path
from unittest import skip

import screwdrivercd.documentation.exceptions
import screwdrivercd.documentation.plugin
import screwdrivercd.documentation.mkdocs.plugin
import screwdrivercd.documentation.sphinx.plugin
import screwdrivercd.utility.environment

from . import ScrewdriverTestCase


# Simple sphinx project directory
sphinx_project =  {
    'doc/source/conf.py': b"""# -*- coding: utf-8 -*-
import os
extensions = []
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'foo'
copyright = ''
version = '0.0.0'
release = version
""",
    'doc/source/index.rst': b"""Test file"""
}


mkdocs_project_config = {
    'mkdocs.yml': b'site_name: test\nsite_url: https://foo.bar.com/\nstrict: true\nnav:\n    - foo: foo.md\n',
    'docs/index.md': b"# Test file\n",
    'docs/foo.md': b"# Test file\n",
}

mkdocs_project_config_fail = {
    'mkdocs.yml': b'site_name: test\nsite_url: https://foo.bar.com/\nstrict: true\nnav:\n    - foo: foo2.md\n',
    'docs/index.md': b"# Test file\n",
    'docs/foo.md': b"# Test file\n",
}


class BuildDocsTestCase(ScrewdriverTestCase):
    def _init_test_repo(self):
        os.system('git init')
        os.system('git config user.email "foo@bar.com"')
        os.system('git config user.name "foo the bar"')
        os.system('git remote add origin https://github.com/yahoo/python-screwdrivercd.git')

    def test__doc_build(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config)
        screwdrivercd.documentation.plugin.build_documentation()

    def test__doc_build_fail(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config_fail)
        with self.assertRaises(screwdrivercd.documentation.exceptions.DocBuildError):
            screwdrivercd.documentation.plugin.build_documentation()

    def test__doc_publish(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config)
        screwdrivercd.documentation.plugin.publish_documentation(push=False)

    def test__doc_publish_fail(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config_fail)
        with self.assertRaises(screwdrivercd.documentation.exceptions.DocPublishError):
            screwdrivercd.documentation.plugin.publish_documentation(push=False)
            os.system('ls -lhR')
            log_dir = Path(screwdrivercd.utility.environment.standard_directories()['logs']) / Path('documentation')
            if os.path.exists(log_dir):
                print('Logs')
                os.system(f'ls -lh {log_dir}')
                print('Log content')
                os.system(f'cat {log_dir}/*')


class PluginsTestCase(ScrewdriverTestCase):

    def test__documentation_plugins__present(self):
        names = [_.name for _ in screwdrivercd.documentation.plugin.documentation_plugins()]
        self.assertIn('mkdocs', names)
        self.assertIn('mkdocs_venv', names)
        self.assertIn('sphinx', names)


class DocumentationPluginTestCase(ScrewdriverTestCase):
    plugin_class = screwdrivercd.documentation.plugin.DocumentationPlugin

    def _create_test_repo_contents(self):
        pass

    def _init_test_repo(self):
        os.system('git init')
        os.system('git config user.email "foo@bar.com"')
        os.system('git config user.name "foo the bar"')
        os.system('git remote add origin https://github.com/yahoo/python-screwdrivercd.git')

    def test__get_clone_url(self):
        self._init_test_repo()
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        result = p.get_clone_url()
        self.assertEqual(result, 'https://github.com/yahoo/python-screwdrivercd.git')

    def test__get_clone_dir(self):
        self._init_test_repo()
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        result = p.get_clone_dir()
        self.assertEqual(result, os.path.abspath('python-screwdrivercd'))

    def test__clone_url(self):
        self._init_test_repo()
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        result = p.clone_url
        self.assertEqual(result, 'https://github.com/yahoo/python-screwdrivercd.git')

    def test__clone_dir(self):
        self._init_test_repo()
        p =  screwdrivercd.documentation.plugin.DocumentationPlugin()
        result = p.clone_dir
        self.assertEqual(result, os.path.abspath('python-screwdrivercd'))

    def test__git_add_all(self):
        self._init_test_repo()
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        Path('testfile.md').touch()
        p.git_add_all()

    def test__disable_jekyll(self):
        self._init_test_repo()
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        p.disable_jekyll()

    def test_documentation_base_plugin_is_present(self):
        p = screwdrivercd.documentation.plugin.DocumentationPlugin()
        self.assertFalse(p.documentation_is_present)

    def test_documentation_base__log_message__default(self):
        p = self.plugin_class()
        p.build_log_filename = 'foo.log'
        p._log_message('foo')
        self.assertTrue(os.path.exists('foo.log'))
        with open('foo.log') as log:
            self.assertEqual('foo\n', log.read())

    def test_documentation_base__log_message__log_filename(self):
        p = self.plugin_class()
        p.build_log_filename = 'foo2.log'
        p._log_message('foo', log_filename='foo.log')
        self.assertTrue(os.path.exists('foo.log'))
        with open('foo.log') as log:
            self.assertEqual('foo\n', log.read())

    def test_documentation_base__log_message__pass_end(self):
        p = self.plugin_class()
        p._log_message('foo', log_filename='logs/foo.log', end='\r\n')
        self.assertTrue(os.path.exists('logs/foo.log'))
        with open('logs/foo.log', 'rb') as log:
            self.assertEqual(b'foo\r\n', log.read())

    def test_documentation_base__log_message_pass_log_filename(self):
        p = self.plugin_class()
        p.build_log_filename = 'foo.log'
        p._log_message('foo', log_filename='foo2.log')
        self.assertTrue(os.path.exists('foo2.log'))
        with open('foo2.log') as log:
            self.assertEqual('foo\n', log.read())

    def test_documentation__base__run_command(self):
        p = self.plugin_class()
        p.build_log_filename = 'foo.log'
        p._run_command(['echo', 'hello'], log_filename=p.build_log_filename)
        self.assertTrue(os.path.exists('foo.log'))
        with open('foo.log') as log:
            self.assertEqual('hello\n', log.read())

    def test_documentation__base__run_command__error(self):
        p = self.plugin_class()
        p.build_log_filename = 'foo.log'
        with self.assertRaises(screwdrivercd.documentation.exceptions.DocBuildError):
            p._run_command(['./exit', '1'], log_filename=p.build_log_filename)

    def test__documentation__build(self):
        self._create_test_repo_contents()
        self.write_config_files(mkdocs_project_config)
        p = self.plugin_class()
        p.build_documentation()
        self.assertTrue(os.path.exists(f'{p.log_dir}/{p.name}.build.log'))

    def test__remove_build_log(self):
        p = self.plugin_class()
        p.build_log_filename = os.path.join(self.tempdir.name, 'build.log')
        Path(p.build_log_filename).touch()
        self.assertTrue(os.path.exists(p.build_log_filename))
        p.remove_build_log()
        self.assertFalse(os.path.exists(p.build_log_filename))

    def test__remove_publish_log(self):
        p = self.plugin_class()
        p.publish_log_filename = os.path.join(self.tempdir.name, 'publish.log')
        Path(p.publish_log_filename).touch()
        self.assertTrue(os.path.exists(p.publish_log_filename))
        p.remove_publish_log()
        self.assertFalse(os.path.exists(p.publish_log_filename))

    def test__clean_directory(self):
        p = self.plugin_class()
        testdir = Path(self.tempdir.name) / 'testdir'
        testdir.mkdir(exist_ok=True)
        testfile = testdir / 'testfile'
        testfile.touch()
        p.clean_directory(str(testdir))
        self.assertFalse(testfile.exists())

    def test__copy_contents(self):
        dir1 = Path(self.tempdir.name) / 'dir1'
        dir2 = Path(self.tempdir.name) / 'dir2'
        srctestfile = dir1 / 'testfile'
        srctestdotfile = dir1 / '.testfile'
        dsttestfile = dir2 / 'testfile'
        dsttestdotfile = dir2 / '.testfile'

        dir1.mkdir(exist_ok=True)
        dir2.mkdir(exist_ok=True)
        srctestfile.touch()
        srctestdotfile.touch()

        p = self.plugin_class()
        p.copy_contents(str(dir1), str(dir2))

        self.assertTrue(dsttestfile.exists())
        self.assertTrue(dsttestdotfile.exists())

    def test__documentation__publish(self):
        instance = self.plugin_class()
        instance.publish_documentation(push=False)

    def test_git_command_timeout_valid(self):
        os.environ['DOCUMENTATION_GIT_TIMEOUT'] = '600'
        p = self.plugin_class()
        self.assertEqual(p.git_command_timeout, 600)

    def test_git_command_timeout_invalid_type(self):
        os.environ['DOCUMENTATION_GIT_TIMEOUT'] = 'invalid'
        p = self.plugin_class()
        self.assertEqual(p.git_command_timeout, 300)  # Default value

    def test_git_command_timeout_not_set(self):
        if 'DOCUMENTATION_GIT_TIMEOUT' in os.environ:
            del os.environ['DOCUMENTATION_GIT_TIMEOUT']
        p = self.plugin_class()
        self.assertEqual(p.git_command_timeout, 300)  # Default value


class SphinxDocumentationPluginTestCase(DocumentationPluginTestCase):
    plugin_class = screwdrivercd.documentation.sphinx.plugin.SphinxDocumentationPlugin

    def _create_test_repo_contents(self):
        pass

    def test__documentation__build(self):
        pass

    def test__documentation__publish(self):
        self.write_config_files(sphinx_project)
        super().test__documentation__publish()


class MkdocsDocumentationPluginTestCase(DocumentationPluginTestCase):
    plugin_class = screwdrivercd.documentation.mkdocs.plugin.MkDocsDocumentationPlugin

    def _create_test_repo_contents(self):
        pass

    def test__documentation__publish(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config)
        super().test__documentation__publish()

    def test_get_sha1_hashes(self):
        # Create test files
        file_contents = {
            '.git/foo': b'Git file',
            'file1.txt': b'Hello, World!',
            'file2.txt': b'Test file content',
            'subdir/file3.txt': b'Subdirectory file content'
        }
        self.write_config_files(file_contents)
        os.link('file1.txt', 'file1_link.txt')

        # Compute expected SHA1 hashes
        expected_hashes = {}
        for filename, content in file_contents.items():
            if filename.startswith('.git'):
                continue
            if Path(filename).is_file():
                file_hash = hashlib.sha1(content).hexdigest()
                expected_hashes[filename] = file_hash

        expected_hashes['file1_link.txt'] = '0a0a9f2a6772942557ab5355d76af442f8f65e01'

        plugin = self.plugin_class()

        # Get actual SHA1 hashes using the method
        actual_hashes = plugin.get_sha1_hashes(self.tempdir.name)

        print('Expected', expected_hashes)
        print('Actual', actual_hashes)

        # Verify the results
        self.assertDictEqual(expected_hashes, actual_hashes)

    def test__diff_dictionaries(self):
        # Create test files
        file_contents = {
            'file1.txt': b'Hello, World!',
            'file2.txt': b'Test file content',
            'subdir/file3.txt': b'Subdirectory file content'
        }
        self.write_config_files(file_contents)

        plugin = self.plugin_class()

        # Get actual SHA1 hashes using the method
        before_hashes = plugin.get_sha1_hashes(self.tempdir.name)

        # Add a file
        with open('file4.txt', 'wb') as fh:
            fh.write(b'Added Test file content\n')

        # Update a file
        with open('file2.txt', 'wb') as fh:
            fh.write(b'Updated Test file content')

        # Delete a file
        os.remove('file1.txt')

        after_hashes = plugin.get_sha1_hashes(self.tempdir.name)
        diff_hashes = plugin.diff_dictionaries(before_hashes, after_hashes)

        self.assertIn('file4.txt', diff_hashes['added'])
        self.assertIn('file2.txt', diff_hashes['changed'])
        self.assertIn('file1.txt', diff_hashes['removed'])


class MkdocsDocumentationVenvPluginTestCase(DocumentationPluginTestCase):
    plugin_class = screwdrivercd.documentation.mkdocs.plugin.MkDocsDocumentationVenvPlugin

    def _create_test_repo_contents(self):
        pass

    def test__documentation__publish(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config)
        super().test__documentation__publish()

    def test__documentation__publish__unchanged(self):
        self._init_test_repo()
        self.write_config_files(mkdocs_project_config)
        p = self.plugin_class()
        p.build_setup()
        p.build_documentation()
        p.build_cleanup()
        p.publish_documentation(push=False)
        os.system(f'git checkout {p.publish_branch}')
        p.build_setup()
        p.build_documentation()
        p.build_cleanup()
        p.publish_documentation(push=False)
