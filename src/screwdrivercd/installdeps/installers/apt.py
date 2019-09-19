# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Install rpm dependencies"""
import logging
import os
import shutil
import subprocess  # nosec - All subprocess calls use full path
from typing import List

from termcolor import colored

from ..installer import Installer


LOG = logging.getLogger(__name__)


class AptInstaller(Installer):
    """
    Debian/Ubuntu Package Installer
    """
    install_command: List[str] = ['apt-get', 'install', '-y']
    install_repo_command: List[str] = ['add-apt-repository']
    config_section: str = 'apt-get'
    install_command_path: List[str] = ['/usr/bin']
    supports_repositories: bool = True
    _repo_tool_install_failed: bool = False
    _updated_index: bool = False

    def update_index(self):  # pragma: no cover - Function is OS specific
        """
        Method to update the package index
        """
        if self._updated_index:
            return
        subprocess.check_call([self.install_command[0], 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
        self._updated_index = True

    def install_repo_tool(self):  # pragma: no cover - Function is OS specific
        """
        Install the repo install tool
        """
        if self.install_repo_command[0].startswith('/') or self._repo_tool_install_failed:
            return

        install_repo_command = shutil.which(self.install_repo_command[0])
        if install_repo_command:
            self.install_repo_command[0] = install_repo_command

        if not os.path.exists(self.install_repo_command[0]):
            LOG.debug(f'Tool to add repos, {self.install_repo_command[0]!r} is missing, trying to install it')
            subprocess.check_call([self.install_command[0], 'install', '-y', 'software-properties-common'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
            install_repo_command = shutil.which(self.install_repo_command[0])
            if install_repo_command:
                self.install_repo_command[0] = install_repo_command
            else:
                self._repo_tool_install_failed = True
                raise FileNotFoundError(f'Could not find the {self.install_repo_command[0]} utility')

    def add_repo(self, repo_name, repo_url):  # pragma: no cover - Function is OS specific
        """
        Add apt repos specified in the configuration
        """
        try:
            self.install_repo_tool()
        except FileNotFoundError:
            message = f'The {self.install_repo_command[0]} utility is missing and cannot be installed, cannot add the {repo_name} repository'
            if self.print_output:
                print(colored(message, 'red'), flush=True)
            else:
                LOG.error(message)
            return

        if self.print_output:
            print(f'Enabling {repo_name!r} repo: ', end='', flush=True)
        try:
            subprocess.check_call(self.install_repo_command + [repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
            if self.print_output:
                print(colored('Ok', 'green'), flush=True)
        except subprocess.CalledProcessError:
            if self.print_output:
                print(colored('Failed', 'red'), flush=True)
            else:
                LOG.error(f'Adding {repo_name!r} repo failed')
