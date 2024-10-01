# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Functions for working with the setup.py file"""
import configparser
import logging
import os
import tomllib

import tomlkit


LOGGER_NAME = 'setup' if __name__ == '__main__' else __name__
LOG = logging.getLogger(LOGGER_NAME)


def setupcfg_has_metadata(setup_cfg_filename=''):
    """Parse the setup.cfg and return True if it has a metadata section"""
    if not setup_cfg_filename:
        if os.path.exists('setup.cfg'):
            setup_cfg_filename = 'setup.cfg'
        elif os.path.exists('pyproject.toml'):
            setup_cfg_filename = 'pyproject.toml'
    if setup_cfg_filename.endswith('.toml'):
        with open(setup_cfg_filename, 'rb') as fh:
            data = tomllib.load(fh)
            if 'project' in data and 'version' in data['project']:
                return True
    else:
        config = configparser.ConfigParser()
        config.read(setup_cfg_filename)
        if 'metadata' in config.sections():
            return True
    return False
