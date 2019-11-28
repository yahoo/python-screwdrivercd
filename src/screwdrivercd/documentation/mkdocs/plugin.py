"""
MkDocs documentation generation plugin
"""
import os

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
