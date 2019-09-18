# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Install brew dependencies"""
import logging
from typing import List

from ..installer import Installer


LOG = logging.getLogger(__name__)


class BrewInstaller(Installer):
    """
    OSX Homebrew Installer
    """
    install_command: List[str] = ['brew', 'install']
    config_section: str = 'brew'
    install_command_path: List[str] = ['/usr/local/bin']
