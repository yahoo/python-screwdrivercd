# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Install apk dependencies"""
import logging
from typing import List

from ..installer import Installer


LOG = logging.getLogger(__name__)


class ApkInstaller(Installer):
    """
    Alpine Package Installer
    """
    install_command: List[str] = ['apk', 'add']
    config_section: str = 'apk'
    install_command_path: List[str] = ['/sbin']
