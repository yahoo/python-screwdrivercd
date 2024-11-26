# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Versioning plugin classes"""
import configparser
import logging
import os
import subprocess  # nosec
from datetime import datetime
from typing import Dict, List, Union

import tomlkit

from .exceptions import VersionError

LOG = logging.getLogger(__name__)


setup_config_files: Dict[str, str] = {
    'setupcfg': 'setup.cfg',
    'toml': 'pyproject.toml'
}


class Version:
    """
    Base Screwdriver Versioning class
    """
    name: Union[str, None] = None
    default_version: List[str] = ['0', '0', '0']
    _meta_version: str = ''

    def __init__(self, setup_cfg_filename=None, ignore_meta_version: bool = False, update_sdv4_meta: bool = True, meta_command: str = 'meta', link_to_project: bool = False):
        self.setup_cfg_filename = setup_cfg_filename
        self.meta_command = meta_command
        self.ignore_meta_version = ignore_meta_version
        self.update_sdv4_meta = update_sdv4_meta
        self.link_to_project = link_to_project
        if not self.setup_cfg_filename:
            self.setup_cfg_filename = setup_config_files[self.setup_cfg_format]

    def __repr__(self):
        return repr(self.version)

    def __str__(self):
        return self.version

    @staticmethod
    def get_env(env_vars, default_value=None):
        """
        Return the value from a list of environment variables searched in order
        returning the default value if a value is not found.

        Parameters
        ----------
        env_vars: str or list of str
            List of environment variables to search
        default_value: str
            Value to return if no environment variables are found

        Returns
        -------
        str:
            Returns the value of the first matching environemnt variable
            or the value of default_value if not found.
        """
        if isinstance(env_vars, str):
            env_vars = [env_vars]
        for env_var in env_vars:
            value = os.environ.get(env_var)
            if value is not None:
                LOG.debug(f"Found env variable {env_var}={value!r}")
                return value
        return default_value

    @property
    def setup_cfg_format(self):
        """
        Parse the configuration file and return the format
        """
        if not self.setup_cfg_filename:
            if os.path.exists('pyproject.toml'):
                with open('pyproject.toml', 'rb') as fh:
                    try:
                        data = tomlkit.load(fh)
                        if 'tool' in data and 'sdv4_version' in data['tool']:
                            self.setup_cfg_filename = 'pyproject.toml'
                            return 'toml'
                    except tomlkit.exceptions.ParseError:
                        print('Unable to parse pyproject.toml')
                        pass

            if os.path.exists('setup.cfg'):
                self.setup_cfg_filename = 'setup.cfg'
                return 'setupcfg'

        if self.setup_cfg_filename and os.path.exists(self.setup_cfg_filename):
            with open(self.setup_cfg_filename, "rb") as fh:
                try:
                    data = tomlkit.load(fh)
                    if 'tool' in data and 'sdv4_version' in data['tool'] and 'project' in data and 'version' in data['project']:
                        if not self.setup_cfg_filename:  # pragma: no cover
                            self.setup_cfg_filename = 'pyproject.toml'
                        return 'toml'
                    else:
                        LOG.info(f'Configuration file {self.setup_cfg_filename} does not contain all screwdriver version configuration settings {data!r}')
                        self.setup_cfg_filename = 'setup.cfg'
                except tomlkit.exceptions.ParseError:
                    LOG.debug(f'Unable to parse configuration file {self.setup_cfg_filename} as toml')
        else:
            self.setup_cfg_filename = 'setup.cfg'
        return 'setupcfg'

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
        if self.setup_cfg_format == 'setupcfg':
            return self.read_setup_version_setupcfg()
        return self.read_setup_version_toml()

    def read_setup_version_toml(self):
        """
        Read the package version from the setup.cfg file

        Returns
        -------
        str:
            The version number from the setup.cfg [metadata] section or the default version if the version is not
            present.
        """
        with open('pyproject.toml', 'rb') as fh:
            try:
                data = tomlkit.load(fh)
            except tomlkit.exceptions.ParseError:  # pragma: no cover
                data = {}
        if 'project' not in data:  # pragma: no cover
            return self.default_version
        return data['project'].get('version', self.default_version).split('.')

    def read_setup_version_setupcfg(self):
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

    def get_link_to_project_using_hash(self):
        """
        Generate and return link to build-triggering commit using its SHA hash
        """
        scm_url = os.environ.get('SCM_URL', '')
        sha = self.get_env(['SD_BUILD_SHA', 'GITHUB_SHA'], '')
        if self.link_to_project and scm_url and sha:
            if scm_url.startswith('git@'):
                hostname = scm_url.split(':')[0].split('@')[1]
                path = ':'.join(scm_url.split(':')[1:])
                return f'https://{hostname}/{path}/tree/{sha}'
            else:
                return f'{scm_url}/tree/{sha}'
        return ''

    def update_setup_cfg_metadata(self):
        """
        Update the version value in the setup.cfg file
        """
        if self.setup_cfg_format == 'setupcfg':
            return self.update_setup_cfg_metadata_setupcfg()
        return self.update_setup_cfg_metadata_toml()

    def update_setup_cfg_metadata_toml(self):
        """
        Update the version value in the pyproject.toml file
        """
        if not self.version:  # pragma: no cover
            LOG.debug(f'New version not available, not updating {self.setup_cfg_filename}')
            return
        LOG.debug(f'Loading toml config file {self.setup_cfg_filename}')
        with open(self.setup_cfg_filename, 'rb') as fp:
            config = tomlkit.load(fp)

        if 'project' not in config:  # pragma: no cover
            LOG.error('The pyproject.toml is lacking a project section, cannot update version')
            return

        config['project']['version'] = self.version

        LOG.debug(f'Writing toml {self.setup_cfg_filename} with the following data {config!r}')
        with open(self.setup_cfg_filename, 'w') as config_file_handle:
            tomlkit.dump(config, config_file_handle)

        LOG.debug(f'Comitting changed config file {self.setup_cfg_filename}')
        self.commit_changed_setup_cfg()

    def update_setup_cfg_metadata_setupcfg(self):
        """
        Update the version value in the setup.cfg file
        """
        if not self.version:  # pragma: no cover
            return
        link_to_project = self.get_link_to_project_using_hash()
        config = configparser.ConfigParser()
        config.read(self.setup_cfg_filename)
        if 'metadata' not in config.sections():
            config['metadata'] = {}

        config['metadata']['version'] = self.version
        if link_to_project:
            project_urls_str = config['metadata'].get('project_urls', '')
            project_urls_dict = {}
            if project_urls_str:
                for entry in project_urls_str.split(os.linesep):
                    entry = entry.strip()
                    if '=' in entry:
                        key, value = entry.split('=')
                        key = key.strip()
                        value = value.strip()
                        project_urls_dict[key] = value

            project_urls_dict['Source'] = link_to_project

            project_urls_str = '\n'
            for key, value in project_urls_dict.items():
                project_urls_str += f'{key} = {value}\n'

            config['metadata']['project_urls'] = project_urls_str.rstrip('\n')

        with open(self.setup_cfg_filename, 'w') as config_file_handle:
            config.write(config_file_handle)

        self.commit_changed_setup_cfg()

    def update_meta_version(self):  # noqa
        """
        Update the meta_version value based on the generated version and pull_request_number
        """
        if not self.meta_version:  # pragma: no cover
            if not self.pull_request_number:
                new_version = self.generated_version
            else:  # pragma: no cover
                new_version = f'{self.generated_version}a{self.pull_request_number}'
            print(f'Updating the screwdriver metadata: package.version={new_version}', flush=True)
            self.meta_version = new_version

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
            prnum = int(self.get_env(['SD_PULL_REQUEST', 'GITHUB_REF'], None))
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
    def meta_version(self) -> str:
        """
        The version from the screwdriver metadata package.version value or None if not present.
        """
        if self.ignore_meta_version:
            return ''
        if self._meta_version:  # pragma: no cover
            return self._meta_version
        LOG.debug(f'Running: {self.meta_command} get package.version')
        try:  # pragma: no cover
            self._meta_version = subprocess.check_output([self.meta_command, 'get', 'package.version']).decode(errors='ignore').strip()  # nosec
        except (FileNotFoundError, PermissionError, subprocess.CalledProcessError):  # pragma: no cover
            pass
        if self._meta_version == 'null':
            self._meta_version = ''
        return self._meta_version  # pragma: no cover

    @meta_version.setter
    def meta_version(self, new_version):
        """
        Set the version in the screwdriver metadata.
        """
        if not self.update_sdv4_meta:  # pragma: no cover
            return
        try:
            subprocess.check_call([self.meta_command, 'set', 'package.version', new_version])  # nosec
        except FileNotFoundError:  # pragma: no cover
            LOG.warning('The screwdriver meta command is missing, unable to set version in screwdriver metadata')
        self._meta_version = new_version

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


class VersionManualUpdate(Version):
    """
    Version updater that just reads the setup.cfg and takes the `version`
    number from `metadata` section. Be aware when using this updater, as this
    updater does not add any unique identifier to the version number.

    It is thus the caller's responsibility to ensure uniqueness is maintained
    during version update.
    """
    name: str = 'manual_update'


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
        """Method to return a newly generated revision value"""
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
        revision = self.get_env(['SD_BUILD', 'SD_BUILD_ID', 'GITHUB_RUN_ID'])
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
        revision = self.get_env(['SD_BUILD', 'SD_BUILD_ID', 'GITHUB_RUN_ID'], '')
        if not revision:
            raise VersionError('Unable to generate version, no SD_BUILD or SD_BUILD_ID value set in the environment variables')
        return [f'{str(now.year)[-2:]}', f'{now.month}', revision]


class VersionDateGHABuild(VersionDateSDV4Build):
    """
    Version updater that generates a version based on the current year and month and the screwdriver build ID
    """
    name = 'github_actions_date'


versioners = {
    'default': VersionGitRevisionCount,
    VersionDateGHABuild.name: VersionDateGHABuild,
    VersionDateSDV4Build.name: VersionDateSDV4Build,
    VersionGitRevisionCount.name: VersionGitRevisionCount,
    VersionManualUpdate.name: VersionManualUpdate,
    VersionSDV4Build.name: VersionSDV4Build,
    VersionUTCDate.name: VersionUTCDate,
}

# Make sure the versioners are listed all lowercase to make identifying them easier
for key, value in list(versioners.items()):
    if key.lower() not in versioners.keys():
        versioners[key.lower()] = value
