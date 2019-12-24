# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Versioning plugin classes"""
import configparser
import logging
import os
import subprocess  # nosec
from datetime import datetime
from typing import List, Union
from .exceptions import VersionError


LOG = logging.getLogger(__name__)


class Version:
    """
    Base Screwdriver Versioning class
    """
    name: Union[str, None] = None
    default_version: List[str] = ['0', '0', '0']
    setup_cfg_filename: str = 'setup.cfg'

    def __init__(self, setup_cfg_filename=None, ignore_meta_version=False, update_sdv4_meta=True):
        if setup_cfg_filename:  # pragma: no cover
            self.setup_cfg_filename = setup_cfg_filename
        self.ignore_meta_version = ignore_meta_version
        self.update_sdv4_meta = update_sdv4_meta

    def __repr__(self):
        return repr(self.version)

    def __str__(self):
        return self.version

    def commit_changed_setup_cfg(self):  # pragma: no cover
        """
        Git commit the setup.cfg
        """
        try:
            output = subprocess.check_output(['git', 'commit', '-m', 'Updated version', self.setup_cfg_filename])  # nosec
            LOG.debug(f'Git commit output {output}')
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    def read_setup_version(self):
        """
        Read the package version from the setup.cfg file

        Returns
        -------
        str:
            The version number from the setup.cfg [metadata] section or the default version if the version is not
            present.
        """
        config = configparser.ConfigParser()
        config.read(self.setup_cfg_filename)
        if 'metadata' in config.sections():
            return config['metadata'].get('version', '').split('.')
        return self.default_version

    def generate(self):
        """
        Generate the version
        """
        return self.read_setup_version()

    def update_setup_cfg_metadata(self):
        """
        Update the version value in the setup.cfg file
        """
        if not self.version:  # pragma: no cover
            return
        config = configparser.ConfigParser()
        config.read(self.setup_cfg_filename)
        if 'metadata' not in config.sections():
            config['metadata'] = {}

        config['metadata']['version'] = self.version

        with open(self.setup_cfg_filename, 'w') as config_file_handle:
            config.write(config_file_handle)

        self.commit_changed_setup_cfg()

    def update_meta_version(self):  # noqa
        """
        Update the meta_version value based on the generated version and pull_request_number
        """
        if not self.meta_version:  # pragma: no cover
            if not self.pull_request_number:
                self.meta_version = self.generated_version
            else:  # pragma: no cover
                self.meta_version = f'{self.generated_version}a{self.pull_request_number}'

    @property
    def pull_request_number(self):
        """
        Return the Pull request number from the Screwdriver SD_PULL_REQUEST env variable if present, returns 0
        if it is not present.
        
        Returns
        -------
        int:
            Pull request number or 0 if not running from a pull request
        """
        try:
            prnum = int(os.environ.get('SD_PULL_REQUEST', None))
        except (TypeError, ValueError):
            prnum = 0
        return prnum

    @property
    def generated_version(self):
        """
        The generated version
        """
        return '.'.join(self.generate())

    @property
    def meta_version(self):
        """
        The version from the screwdriver metadata package.version value or None if not present.
        """
        if self.ignore_meta_version:
            return None
        try:  # pragma: no cover
            version = subprocess.check_output(['meta', 'get', 'package.version']).decode(errors='ignore').strip()  # nosec
        except FileNotFoundError:  # pragma: no cover
            version = None
        if not version or version == 'null':  # pragma: no cover
            version = None
        return version  # pragma: no cover

    @meta_version.setter
    def meta_version(self, new_version):
        if not self.update_sdv4_meta:  # pragma: no cover
            return
        try:
            subprocess.check_call(['meta', 'set', 'package.version', new_version])  # nosec
        except FileNotFoundError:  # pragma: no cover
            LOG.warning('The screwdriver meta command is missing, unable to set version in screwdriver metadata')

    @property
    def version(self):
        """
        The version from the versioner, will be the version from the screwdriver package.version if it is set, otherwise
        it will be the generated version number from the versioner.
        """
        if self.meta_version:  # pragma: no cover
            return self.meta_version

        ver = self.generated_version
        if not self.pull_request_number:
            return ver
        return f'{ver}a{self.pull_request_number}'


class VersionUpdateRevision(Version):
    """
    Version updater that updates the revision (last component) of a semetic version.
    """
    log_errors: bool = True
    default_revision_value: str = '0'
    
    def __init__(self, *args, **kwargs):
        self.log_errors = kwargs.pop('log_errors', self.log_errors)
        super().__init__(*args, **kwargs)

    def revision_value(self):  # pragma: no cover
        "Method to return a newly generatated revision value"
        return self.default_revision_value

    def generate(self):  # pragma: no cover
        version = super().generate()
        if version:
            try:
                version[-1] = self.revision_value()
            except VersionError as error:
                if self.log_errors:
                    LOG.exception(f'Unable to get revision value for versioner {self.name!r}')
                else:
                    raise error
        return version


class VersionGitRevisionCount(VersionUpdateRevision):
    """
    Version Revision updater that sets the revision number to be equal to the number of git commits of the current
    repository.
    
    Each new git commit will increment the revision value.
    
    Notes
    -----
    This Versioner may not work correctly if the current git repository is a shallow git clone.
    """
    name: str = 'git_revision_count'

    def revision_value(self):
        """
        Get a count of the number of git commits and return the count
        Returns
        -------
        int
            Revision count or None if git was not found
        """
        try:
            result = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).decode(errors='ignore')  # nosec
        except subprocess.CalledProcessError:  # pragma: no cover
            try:  # pragma: no cover
                result = len(subprocess.check_output(['git', 'rev-list', 'HEAD']).decode(errors='ignore').split('\n'))  # nosec
            except subprocess.CalledProcessError:
                raise VersionError('Unable to generate a version from the git revision count')
        try:
            result = int(result)
        except ValueError:  # pragma: no cover
            raise VersionError('Got invalid response from the git rev-list command')
        return str(result)


class VersionSDV4Build(VersionUpdateRevision):
    """
    Version Revision updater that sets the revision number to be equal to the value of the screwdriver SD_BUILD number.
    
    Each new screwdriver job run will increment the revision number.
    """
    name = 'sdv4_SD_BUILD'
    def revision_value(self):
        revision = os.environ.get('SD_BUILD', None)
        if not revision:
            LOG.debug('No value for SD_BUILD found')
            revision = os.environ.get('SD_BUILD_ID', None)
        if not revision:
            raise VersionError('Unable to generate version, no SD_BUILD or SD_BUILD_ID value set in the environment variables')
        return revision


class VersionUTCDate(Version):
    """
    Version updater that generates a version based on the current UTC date/time.
    
    Each new screwdriver job will get a version based on the current date and time.
    """
    name = 'utc_date'
    now = None

    def __init__(self, *args, **kwargs):
        self.now = kwargs.pop('now', None)
        super().__init__(*args, **kwargs)

    def generate(self):
        now = datetime.utcnow()
        if self.now:  # pragma: no cover
            now = self.now
        return [f'{now.year}', f'{now.month}{now.day:02}', f'{now.hour:02}{now.minute:02}{now.second:02}']


class VersionDateSDV4Build(Version):
    """
    Version updater that generates a version based on the current year and month and the screwdriver build ID
    """
    name = 'sdv4_date'

    def __init__(self, *args, **kwargs):
        self.now = kwargs.pop('now', None)
        super().__init__(*args, **kwargs)

    def generate(self):
        now = self.now if self.now else datetime.utcnow()
        revision = os.environ.get('SD_BUILD', None)
        if not revision:
            revision = os.environ.get('SD_BUILD_ID', None)
        print(f'Revision={revision!r}')
        if not revision:
            raise VersionError('Unable to generate version, no SD_BUILD or SD_BUILD_ID value set in the environment variables')
        return [f'{str(now.year)[-2:]}', f'{now.month}', revision]


versioners = {
    'default': VersionGitRevisionCount,
    VersionGitRevisionCount.name: VersionGitRevisionCount,
    VersionUTCDate.name: VersionUTCDate,
    VersionSDV4Build.name: VersionSDV4Build,
    VersionDateSDV4Build.name: VersionDateSDV4Build
}

# Make sure the versioners are listed all lowercase to make identifying them easier
for key, value in  list(versioners.items()):
    if key.lower() not in versioners.keys():
        versioners[key.lower()] = value
