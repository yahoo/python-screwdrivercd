# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Base Installer Functionality"""
import copy
import logging
import os
import shutil
import subprocess  # nosec - All subprocess calls use full path
import sys
from typing import Dict, Optional, List

from termcolor import colored
from .config import Configuration
from .requirement import Requirement


LOG = logging.getLogger(__name__)


class Installer():
    """Generic Package Installer
    """
    name: str = 'generic'
    """:str: The name of the installer class"""

    install_command: List[str] = ['echo', 'fake', 'install']
    """:obj:`list` of :obj:`str`: The base install command list"""

    bin_dir: Optional[str] = None
    """str: The directory that contains the install command binary, or None to search the PATH"""

    install_command_path: Optional[List[str]] = []
    """:obj:`list` of :obj:`str`: A list of directories to search for the install command"""

    use_system_path: bool = False
    """bool: If True, search the system path if the command cannot be found in the install_command_path"""

    supports_repositories: bool = False
    """bool: If True the installer supports adding repositories"""

    default_repos: Optional[Dict[str, str]] = {}
    """A dictionary of repo name, repo url to enable by default"""

    config_section: str = 'echo'
    """str: The name of the config section that this installer configuration is found in"""

    print_output: bool = False
    """bool: If True, print the output to stdout instead of logging"""

    print_error_output: bool = True
    """bool: If True, print the output to stdout instead of logging when an error occurs"""

    exit_on_missing: bool = False
    """bool: If True, terminate installation immediately if a dependency is missing"""

    def __init__(self, dry_run: bool = False, bin_dir: Optional[str] = None):
        """
        Generic Package Installer

        Parameters
        ----------
        bin_dir: str, optional
            The directory path that contains the binaries

        dry_run: bool, optional
            If True, Don't execute packaging commands, default=False
        """
        self.dry_run = dry_run

        if bin_dir:
            self.bin_dir = bin_dir


        self.config = Configuration()
        self.find_install_command()
        self._handle_custom_settings()

    @property
    def deps_config_keys(self):
        """
        All of the configuration keys that have dependencies for this installer

        Returns
        -------
        list of str
            The settings that contain dependencies to be installed
        """
        # This is a property to allow classes derived from this one to
        # add dependencies to the list returned dynamically depending
        # on system state.
        return ['deps']

    @property
    def has_dependencies(self) -> bool:
        """
        Check if the installer has dependencies to install in the current environment.

        Returns
        =======
        bool:
            True if there are dependencies to install, False otherwise
        """
        for config_key in self.deps_config_keys:
            dependencies = self.config.configuration[self.config_section][config_key]
            if dependencies:
                dependencies = self.filter_environment_markers(dependencies)
                if dependencies:
                    return True
        return False

    @property
    def is_supported(self) -> bool:
        """
        Check for the installer utility and return True if it's present, False otherwise

        Returns
        =======
        bool:
            True if the installer is supported on the host system, False otherwise
        """
        self.find_install_command()
        if os.path.exists(self.install_command[0]):
            return True
        return False

    @property
    def plugin_configuration(self):
        """
        Return the plugin configuration dictionary if it is found

        Returns
        -------
        dict:
            Plugin configuration dictionary
        """
        if not self.config:
            return {}
        if not self.config.configuration:
            return {}
        return self.config.configuration.get(self.config_section, {})

    def _handle_custom_settings(self):
        """
        Allows classes derived from this one to handle custom config options outside of the dependency sections
        Parameters
        ----------
        config
            parsed config dictionary

        Returns
        -------
        """

    def add_repos(self):
        """
        Add repositories to the host configuration
        """
        if not self.supports_repositories:
            LOG.debug(f'Install plugin {self.config_section} does not support repositories')
            return
        repos = copy.copy(self.default_repos)
        repos.update(self.plugin_configuration.get('repos', {}))

        LOG.debug('Adding package repositories')
        for repo_name, repo_url in repos.items():
            repo_url_env = repo_url.split(';')
            if len(repo_url_env) > 1:
                repo_url_req = Requirement(f'{repo_name};{repo_url_env[-1]}')
                LOG.debug(f'Evaluating the repository environment marker {repo_name};{repo_url_env[-1]} == {repo_url_req.env_matches}')
                if not repo_url_req.env_matches:
                    LOG.debug(f'Filtered {repo_name!r} as it is not supported in this environment')
                    continue
                repo_url = repo_url_env[0]
            if self.print_output:
                print(f'Enabling {repo_name!r} repo: ', end='', flush=True)
            else:
                LOG.debug(f'Enabling {repo_name!r} repo')
            self.add_repo(repo_name=repo_name, repo_url=repo_url)

    def add_repo(self, repo_name, repo_url):  # pragma: no cover
        """
        Add a repository to the host configuration

        Parameters
        ----------
        repo_name: str
            The human readable name string for the repository

        repo_url: str
            The url of the repository to add
        """

    def determine_bin_directory(self):
        """
        Determine the bin_dir for the default pip command based on the environment
        """
        if self.bin_dir or self.install_command[0].startswith('/'):
            LOG.debug(f'The command bin_dir {self.bin_dir} is already set')
            return

        if self.plugin_configuration and self.plugin_configuration.get('bin_dir', None):
            LOG.debug('Setting the configuartion directory from the configuration')
            self.bin_dir = self.plugin_configuration['bin_dir']

        # LOG.debug(f'Searching for the install command in {self.install_command_path}')
        for directory in self.install_command_path:
            filename = os.path.join(directory, self.install_command[0])
            if os.path.exists(filename):
                # LOG.debug(f'Found install command in install_command_path {directory!r} directory')
                self.bin_dir = directory
                return

        if self.use_system_path:
            install_binary = shutil.which(self.install_command[0])
            if install_binary:
                self.bin_dir = os.path.dirname(install_binary)
                LOG.debug(f'Found install command in system path {self.bin_dir}')
                return

    def find_install_command(self):
        """
        Find the install command binary to use and update the install command
        """
        self.determine_bin_directory()
        if self.install_command[0].startswith('/'):
            return

        if self.bin_dir:
            full_command = os.path.abspath(os.path.join(self.bin_dir, self.install_command[0]))
            self.install_command[0] = full_command
        else:
            if self.use_system_path:
                LOG.debug(f'Finding the install command in the system PATH')
                install_command = shutil.which(self.install_command[0])
                if install_command:
                    self.install_command[0] = install_command
                return

    def filter_environment_markers(self, dependencies: List[str]) -> List[str]:
        """
        Remove any dependencies that don't match environment markers for the current environment
        """
        new_dependencies = []
        for dependency in dependencies:
            req = Requirement(dependency)
            if not req.env_evals:
                new_dependencies.append(dependency)
                continue

            if req.env_matches:
                dependency = dependency.split(';')[0]
                new_dependencies.append(dependency)
                continue

            LOG.debug(f'Filtered dependency {dependency} due to the environment marker')
        return new_dependencies

    def install_dependencies(self) -> List[str]:
        """
        Install all of the dependencies using the install command
        """
        if not self.has_dependencies:
            LOG.debug(f'No {self.name!r} dependencies to install')
            return []

        self.add_repos()
        self.update_index()

        installed: List[str] = []
        invalid: List[str] = []
        for config_key in self.deps_config_keys:
            LOG.debug(f'Looking for dependencies in [tool.sdv4_installdeps.{self.config_section}] {config_key}')
            dependencies = self.config.configuration[self.config_section][config_key]
            if dependencies:
                dependencies = self.filter_environment_markers(dependencies)
                # LOG.debug(f'Processing dependencies {dependencies!r}')
                invalid += self.invalid_dependencies(dependencies, config_key=config_key)
                if invalid:
                    if self.print_error_output:
                        print(colored('Invalid %r dependencies %r specified' % (config_key, invalid), 'red'), flush=True)
                    else:
                        LOG.error(colored('Invalid %r dependencies %r specified' % (config_key, invalid), 'red'))
                    if self.exit_on_missing:
                        break
                    dependencies = list(set(dependencies) - set(invalid))

                if self.print_output:
                    print(f'Installing dependencies {dependencies!r}')
                else:
                    LOG.debug(f'Installing dependencies: {dependencies!r}')
                installed += self.install(dependencies, config_key=config_key)
        return installed

    def install(self, dependencies, config_key=None):
        """
        Install a list of dependencies

        Parameters
        ----------
        dependencies: list
            List of the dependencies to install

        Returns
        -------
        list:
            Dependencies installed
        """
        command = self.install_command + self.install_arguments(config_key=config_key) + dependencies
        if self.dry_run:
            LOG.debug('Dry Run: %r', ' '.join(command))
            return dependencies
        if self.print_output:
            print('Running command: %r' % ' '.join(command))
        else:  # pragma: no cover
            LOG.debug('Running command: %r', ' '.join(command))
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)  # nosec - All subprocess calls use full path
        except subprocess.CalledProcessError as error:
            if self.print_error_output:
                print(colored(f'Install command {" ".join(command)!r} failed', "red"), flush=True)
                print(error.stdout.decode().strip())
                if self.exit_on_missing:
                    sys.exit(1)
            else:
                LOG.error('Install command failed')
                LOG.error(error.stdout.decode.strip())
            return []

        if self.print_output:
            print(output.decode().strip())
        else:  # pragma: no cover
            LOG.debug(output.decode().strip())

        return dependencies

    def validate_dependency(self, dependency):
        """
        Validate a dependency is valid

        Parameters
        ----------
        dependency: str
            Dependency to validate

        Returns
        -------
        bool
            True if valid
        """
        return True

    def invalid_dependencies(self, dependencies, config_key=None):
        """
        Check that all dependencies in the list are valid

        Parameters
        ----------
        dependencies: list of str:
            The dependency list to validate

        Returns
        -------
        list of str:
            Dependencies that are invalid
        """
        invalid = []
        for depend in dependencies:
            if self.validate_dependency(depend) is False:
                invalid.append(depend)
        return invalid

    def install_arguments(self, config_key=None):
        """
        Return extra command line arguments list based on the config_key

        Returns
        -------
        list of str:
            Extra arguments to add
        """
        return []

    def update_index(self):
        """
        Method to update the package index
        """
