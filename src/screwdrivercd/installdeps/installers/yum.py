# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Install yum dependencies"""
import logging
import os
import shutil
import subprocess  # nosec - All subprocess calls use full path
from typing import Dict, Optional, List

from termcolor import colored

from ..installer import Installer


LOG = logging.getLogger(__name__)


class YumInstaller(Installer):
    """
    Yum Package tool package installer
    """
    install_command: List[str] = ['yum', 'install', '-y']
    install_repo_command: List[str] = ['yum-config-manager', '--add-repo']
    config_section: str = 'yum'
    install_command_path: List[str] = ['/bin', '/usr/bin']
    use_system_path: bool = False
    supports_repositories: bool = True
    default_repos: Optional[Dict[str, str]] = dict()
    _repo_tool_install_failed = False

    def install_repo_tool(self):  # pragma: no cover - Function is OS specific
        """
        Installer the tool needed to add repositories to the system

        Raises
        ------
        FileNotFoundError: The tool was not found after attempting to install it
        """
        if self.install_repo_command[0].startswith('/') or self._repo_tool_install_failed:
            return

        install_command = shutil.which(self.install_repo_command[0])
        if install_command:
            self.install_repo_command[0] = install_command

        if not os.path.exists(self.install_repo_command[0]):
            LOG.debug(f'Tool to add repos, {self.install_repo_command[0]} is missing, trying to install it')
            subprocess.check_call([self.install_command[0], 'install', '-y', 'yum-utils'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
            install_command = shutil.which(self.install_repo_command[0])
            if install_command:
                self.install_repo_command[0] = install_command
            else:
                self._repo_tool_install_failed = True
                raise FileNotFoundError('Could not find the {self.install_repo_command[0]} utility')

    def add_repo(self, repo_name, repo_url):  # pragma: no cover - Function is OS specific
        """
        Add Yum repos specified in the configuration
        """
        try:
            self.install_repo_tool()
        except FileNotFoundError:
            print(colored(f'The yum-config-manager utility is missing and cannot be installed, cannot add the {repo_name} repository', 'red'), flush=True)
            return

        if repo_url.startswith('enable:'):
            repo_name = repo_url[7:]
            if self.print_output:
                print(f'Enabling {repo_name!r} repo: ', end='', flush=True)
            try:
                subprocess.check_call([self.install_repo_command[0], '--enable', repo_name, '--save'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
                if self.print_output:
                    print(colored('Ok', 'green'), flush=True)
            except subprocess.CalledProcessError:
                if self.print_output:
                    print(colored('Failed', 'red'), flush=True)
                else:
                    LOG.error('Enabling repository {repo_name!r} failed')
            return

        if repo_url.startswith('disable:'):
            repo_name = repo_url[8:]
            if self.print_output:
                print(f'Disabling {repo_name!r} repo: ', end='', flush=True)
            try:
                subprocess.check_call([self.install_repo_command[0], '--disable', repo_name, '--save'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
                if self.print_output:
                    print(colored('Ok', 'green'), flush=True)
            except subprocess.CalledProcessError:
                if self.print_output:
                    print(colored('Failed', 'red'), flush=True)
                else:
                    LOG.error('Disabling repository {repo_name!r} failed')
            return

        if self.print_output:
            print(f'Adding {repo_name!r} with url {repo_url!r} repo: ', end='', flush=True)
        else:
            LOG.debug(f'Adding {repo_name!r} with url {repo_url!r} repo')
        try:
            subprocess.check_call(self.install_repo_command + [repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
            if self.print_output:
                print(colored('Ok', 'green'), flush=True)
        except subprocess.CalledProcessError:
            if self.print_output:
                print(colored('Failed', 'red'), flush=True)
            else:
                LOG.error('Adding repository {repo_name!r} failed')

    def validate_dependency(self, dependency):  # pragma: no cover - Function is OS specific
        """
        Validate a dependency is valid
        Parameters
        ----------
        dependency: str
            The package name to validate
        Returns
        -------
        bool
            True if valid
        """
        try:
            subprocess.check_call([self.install_command[0], 'info', dependency], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
        except subprocess.CalledProcessError:
            return False
        return True
