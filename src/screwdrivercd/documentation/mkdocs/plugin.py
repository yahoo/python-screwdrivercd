"""
MkDocs documentation generation plugin
"""
import os
import subprocess  # nosec
import tempfile

from typing import List

from ..plugin import DocumentationPlugin
from ...utility.environment import interpreter_bin_command


class MkDocsDocumentationPlugin(DocumentationPlugin):
    """
    screwdrivercd.documentation plugin for mkdocs documentation
    """
    name = 'mkdocs'
    build_output_dir = ''
    possible_config_files = ['mkdocs.yml', 'docs/mkdocs.yml']

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        self.build_command = [interpreter_bin_command(), '-m', 'mkdocs', 'build', '--config-file', self.config_file, '--site-dir', self.build_dir]

    @property
    def config_file(self) -> str:
        for cfile in self.possible_config_files:
            if os.path.exists(cfile):
                return cfile
        return self.possible_config_files[0]

    @property
    def documentation_is_present(self) -> bool:
        """
        Returns
        =======
        bool:
            Check that the documentation source is present, Returns True if it is, False otherwise
        """
        if os.path.exists(self.config_file):
            return True
        return False


class MkDocsDocumentationVenvPlugin(MkDocsDocumentationPlugin):
    """
    screwdrivercd.documentation plugin for mkdocs documentation in a python venv
    """
    name = 'mkdocs_venv'
    venv_dir: str = ''
    default_requirements: List[str] = ['mkdocs', 'markdown', 'pymdown-extensions', 'markdown-include', 'mkdocs-material', 'pygments']

    def build_setup(self):
        """
        Set up a temporary Python virtualenv before running the build
        """
        self.tempdir = tempfile.TemporaryDirectory()
        self.venv_dir = os.path.join(self.tempdir.name, 'mkdocsvenv')
        self.venv_bin = os.path.join(self.venv_dir, 'bin')
        self.venv_python = os.path.join(self.venv_bin, 'python3')

        subprocess.check_call([interpreter_bin_command(), '-m', 'venv', self.venv_dir])  # nosec

        if os.path.exists('documentation_mkdocs_requirements.txt'):
            requirements_file = 'documentation_mkdocs_requirements.txt'
        else:
            requirements_file = os.path.join(self.tempdir.name, 'documentation_mkdocs_requirements.txt')
            with open(requirements_file, 'w') as fh:
                fh.write('\n'.join(self.default_requirements))

        if os.path.exists(requirements_file):
            self._run_command([self.venv_python, '-m', 'pip', 'install', '-r', requirements_file], log_filename=self.build_log_filename)  # nosec

        self.build_command = [self.venv_python, '-m', 'mkdocs', 'build', '--config-file', self.config_file, '--site-dir', self.build_dir]

    def build_cleanup(self):
        """
        Clean up the temporary virtualenv
        """
        self.tempdir.cleanup()
