"""
Sphinx documentation generation plugin
"""
import os
from ..plugin import DocumentationPlugin
from ...utility.environment import interpreter_bin_command


class SphinxDocumentationPlugin(DocumentationPlugin):
    """
    screwdrivercd.documentation plugin for sphinx documentation
    """
    name = 'sphinx'
    build_dest = 'build/sphinx/html'
    builder = 'html'

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        self.source_dir = os.path.join(self.source_dir, 'doc/source')
        self.build_output_dir = 'build/sphinx/html'
        self.builder = os.environ.get('DOCUMENTATION_SPHINX_BUILDER', self.builder)
        self.build_command = [interpreter_bin_command('sphinx-build'), '-b', self.builder, self.source_dir, self.build_dest]

    @property
    def documentation_is_present(self) -> bool:
        if os.path.exists('doc/source/conf.py'):
            return True
        return False
