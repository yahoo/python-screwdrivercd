# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd package functions
"""
import logging
import os
import subprocess  # nosec
import sys
import tarfile
import tempfile
import zipfile

from typing import Any, Dict

from pyroma.projectdata import run_setup, FakeContext, SetupMonkey
from .exceptions import PackageParseError


logger = logging.getLogger(__name__)


def run_setup_command(command, cli_args=None, stderr_log=None) -> bytes:
    """
    Run the setup command and return the results
    """
    command = [sys.executable, 'setup.py', command]
    if cli_args:
        command += cli_args
    if not stderr_log:  # pragma: no cover
        stderr_log = f'{os.environ.get("SD_ARTIFACTS_DIR", ".")}/logs/artifactory_publish.stderr.log'
    if not os.path.exists(os.path.dirname(stderr_log)):
        os.makedirs(os.path.dirname(stderr_log))
    with open(stderr_log, 'ab') as stderr:
        try:
            result = subprocess.check_output(command, stderr=stderr)  # nosec
        except subprocess.CalledProcessError as error:  # pragma: no cover
            if error.stdout:
                logger.error(f'{error.stdout}')
            raise error
    return result


def setup_query(command, cli_args=None) -> str:
    """
    Run a setup command and return the last line from stdout
    """
    return run_setup_command(command, cli_args=cli_args).decode(errors='ignore').strip().split(os.linesep)[-1].strip()


class PackageMetadata():
    """
    Python package metadata parser
    """
    used_setuptools = False
    _get_package_data_run = False
    metadata: Dict[str, Any] = {}
    options: Dict[str, Any] = {}

    def __init__(self, path=None):
        """
        Parse a python package

        Parameters
        ----------
        path: str, optional
            The path to the package, this can be a directory containing a package or a package archive file
        """
        super().__init__()
        if path:
            self.path = os.path.abspath(path)
        else:  # pragma: no cover
            self.path = os.path.abspath(os.getcwd())
        if os.path.isdir(self.path):  # pragma: no cover
            self.get_package_data()
        else:
            self.extract_package_data()

    def extract_package_data(self, path=None):
        """
        Extract a package archive and update the attributes of this class with it's metadata values.
        """
        # pylint: disable=W0612
        if not path:  # pragma: no cover
            path = self.path
        path = os.path.abspath(path)
        basename, extension = os.path.splitext(path)
        extension = extension.strip('.')
        if basename.endswith('.tar'):
            basename, junk = os.path.splitext(basename)

        basename = os.path.basename(basename)
        with tempfile.TemporaryDirectory() as tempdir:
            destdir = os.path.join(tempdir, basename)
            if extension in ['bz2', 'gz', 'tar', 'tb2', 'tgz']:
                logger.debug(f'Extracting tarfile {path} to {tempdir}')
                tarfile.open(name=path, mode='r:*').extractall(tempdir)
            elif extension in ['zip', 'egg']:
                logger.debug(f'Extracting zipfile {path} to {tempdir}')
                zipfile.ZipFile(path, mode='r').extractall(tempdir)
            else:  # pragma: no cover
                raise PackageParseError(f'Unknown package type {extension}')

            self.get_package_data(path=destdir)

    def get_package_data(self, path=None):
        """
        Updates the attributes of this class with values from the package.
        """
        # Run the imported setup to get the metadata.
        if not path:  # pragma: no cover
            path = self.path

        with FakeContext(path):
            with SetupMonkey() as sm:
                try:
                    distro = run_setup('setup.py', stop_after='config')
                except ImportError:  # pragma: no cover
                    raise PackageParseError('Unable to parse the package setup.py')

                self.used_setuptools = sm.used_setuptools
                for attrib in ['install_requires', 'metadata', 'namespace_packages', 'packages', 'python_requires', 'setup_requires']:
                    if not hasattr(distro, attrib):  # pragma: no cover
                        logging.debug(f'{attrib} is missing from distro object')
                        setattr(self, attrib, None)
                        continue

                    src_attrib = getattr(distro, attrib)
                    if not hasattr(src_attrib, '__dict__'):
                        setattr(self, attrib, src_attrib)
                        continue

                    dest_attrib_dict = {}
                    setattr(self, attrib, dest_attrib_dict)
                    src_attrib_dict = src_attrib.__dict__
                    for key, value in src_attrib_dict.items():
                        if key[0] == '_' or callable(value):  # pragma: no cover
                            continue
                        if not value:
                            dest_attrib_dict[key] = value
                            continue
                        dest_attrib_dict[key] = value

                self.command_options = distro.command_options
                self.options = self.command_options.get('options', {})
                for key, value in self.command_options.get('options', {}).items():
                    if isinstance(value, tuple):
                        if len(value) == 1:  # pragma: no cover
                            self.options[key] = None
                        elif len(value) == 2:
                            self.options[key] = value[1]
                        else:  # pragma: no cover
                            self.options[key] = value[1:]
                    else:  # pragma: no cover
                        self.options[key] = value

                for option_item in ['install_requires', 'namespace_packages', 'packages', 'python_requires', 'setup_requires']:
                    value = self.options.get(option_item, None)
                    if not value:
                        continue
                    if not isinstance(value, list):
                        self.options[option_item] = []
                        for item in [_.strip() for _ in value.split(os.linesep)]:
                            if item:
                                self.options[option_item].append(item)
                    if not hasattr(self, option_item):  # pragma: no cover
                        setattr(self, option_item, self.options[option_item])

                for option_item in ['include_package_data', 'zip_safe']:
                    value = self.options.get(option_item, None)
                    if not value:
                        continue
                    if value.lower() in ['true', '1', 'on']:  # pragma: no cover
                        self.options[option_item] = True
                    else:  # pragma: no cover
                        self.options[option_item] = False
