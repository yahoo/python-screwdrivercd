# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Functions for working with the setup.py file"""
import configparser
import logging


LOGGER_NAME = 'setup' if __name__ == '__main__' else __name__
LOG = logging.getLogger(LOGGER_NAME)


def setupcfg_has_metadata(setup_cfg_filename='setup.cfg'):
    """Parse the setup.cfg and return True if it has a metadata section"""
    config = configparser.ConfigParser()
    config.read(setup_cfg_filename)
    if 'metadata' in config.sections():
        return True
    return False
