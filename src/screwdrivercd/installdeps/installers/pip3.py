# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Install pip dependencies"""
import logging
from typing import Optional, List

from ..installer import Installer


LOG = logging.getLogger(__name__)


class PipInstaller(Installer):
    """
    Python pip3 package installer
    """
    install_command: List[str] = ['pip3', 'install']
    config_section: str = 'pip3'
    bin_dir: Optional[str] = None
    install_command_path: Optional[List[str]] = [
        # Python platform python
        '/opt/python/bin',

        # Manylinux python
        '/opt/python/cp37-cp37m/bin',
        '/opt/python/cp36-cp36m/bin',
        '/opt/python/cp35-cp35m/bin',

        # Ubuntu/Fedora
        '/usr/bin'
    ]
