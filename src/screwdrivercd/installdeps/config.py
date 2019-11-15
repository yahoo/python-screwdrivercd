# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Read/Parse the configuration file for the screwdrivercd.installdeps tool
"""
import copy
import os

from collections.abc import Mapping  # pylint: disable no-name-in-module
from typing import Any, Dict, Optional

import toml


CONFIGURATION_SCHEMA = {
    'apk': {
        'deps': [],
    },
    'apt-get': {
        'deps': [],
        'repos': {}
    },
    'echo': {
        'deps': []
    },
    'install': ['apk', 'apt-get', 'yinst', 'yum', 'pip3'],
    'pip3': {
        'deps': [],
        'repos': {}
    },
    'yinst': {
        'deps': [],
        'deps_current': [],
        'deps_quarantine': [],
        'deps_stable': [],
        'deps_test': []
    },
    'yum': {
        'deps': [],
        'branch_deps': {},
        'repos': {},
        'setting': {},
    }
}


def deep_update(source, update_dict):
    """
    Merge update_dict values into the source dictionary.
    """
    for key, value in update_dict.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = update_dict[key]
    return source


class Configuration():
    """
    installdeps configuration class
    """
    filename = 'pyproject.toml'
    configuration: Dict[Any, Any] = {}

    def __init__(self, filename: Optional[str] = None):
        if filename:
            self.filename = filename
        self.configuration = copy.deepcopy(CONFIGURATION_SCHEMA)
        self.load_configuration()

    def load_configuration(self):
        """
        Load the configuration from the configuration file
        """
        if not os.path.exists(self.filename):
            return
        
        with open(self.filename) as fh:
            conf = toml.load(fh)

        tool_configs = conf.get('tool', None)
        if not tool_configs:
            return

        sdv4_installdeps_configs = tool_configs.get('sdv4_installdeps', None)
        if not sdv4_installdeps_configs:
            sdv4_installdeps_configs = tool_configs.get('screwdrivercd_installdeps', None)
            if not sdv4_installdeps_configs:
                return

        deep_update(self.configuration, sdv4_installdeps_configs)
