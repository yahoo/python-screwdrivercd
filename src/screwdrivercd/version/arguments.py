# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Command line argument parsing"""
import argparse
import configparser
from .exceptions import VersionError
from .version_types import versioners


def get_config_default(key, default=None, setup_cfg_filename='setup.cfg'):
    """
    Get the default value for a configuration setting

    Parameters
    ==========
    key: str
        The key to read from the configuration

    default: str, optional
        A default value to return if the key is not present in the configuration.

    setup_cfg_filename: str
        The configuration file to parse for the configuration value.
    """
    config = configparser.ConfigParser()
    config.read(setup_cfg_filename)
    if 'screwdrivercd.version' in config.sections():
        return config['screwdrivercd.version'].get(key, default)

    if 'sdv4.version' in config.sections():
        return config['sdv4.version'].get(key, default)

    if 'ouroath.platform_version' in config.sections():  # pragma: no cover
        return config['ouroath.platform_version'].get(key, default)

    return default


def get_bool_equivalent(key) -> bool:
    """ Get the equivalent bool value for a string key in the config file. """

    if isinstance(key, str) and key.lower() in ['false', '0', 'off']:
        return False
    return True


def parse_arguments():
    """
    Parse the command line arguments

    Returns
    -------
    argparse.arguments:
        The parsed arguments
    """
    version_type = get_config_default('version_type', default='default')
    update_meta = get_config_default('update_screwdriver_meta', default='false')
    update_meta = get_bool_equivalent(update_meta)
    link_to_project = get_config_default('link_to_project', default='false')
    link_to_project = get_bool_equivalent(link_to_project)

    version_choices = list(versioners.keys())
    if version_type not in version_choices:
        raise VersionError(f'The version_type in the [screwdrivercd.version] section of setup.cfg has an invalid version type of {version_type!r}')

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--force_update', default=False, action='store_true', help='Update the setup.cfg even if it does not have a metadata section')
    parser.add_argument('--version_type', default=version_type, choices=version_choices, help='Type of version number to generate')
    parser.add_argument('--ignore_meta', default=False, action='store_true', help='Ignore the screwdriver v4 metadata')
    parser.add_argument('--update_meta', default=update_meta, action='store_true', help='Update the screwdriver v4 metadata with the new version')
    parser.add_argument('--link_to_project', default=link_to_project, action='store_true', help='Add/update link to source project tree for current package version')
    result = parser.parse_args()
    return result
