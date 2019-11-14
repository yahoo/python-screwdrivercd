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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build_command = [interpreter_bin_command(), '-m', 'mkdocs', 'build', '--site-dir', self.build_dir]

    @property
    def documentation_is_present(self) -> bool:
        """
        Returns
        =======
        bool:
            Check that the documentation source is present, Returns True if it is, False otherwise
        """
        if os.path.exists('mkdocs.yml'):
            return True
        return False
