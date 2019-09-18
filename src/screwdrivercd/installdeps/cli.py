# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Command line `sdv4_install_deps` utility.

The main() function of this utility provides a command line interface to install Operating system packages based on
the configuration in the `pyproject.toml` file.
"""
import logging
import os
import sys

from termcolor import colored

from .installer import Configuration
from .installers import install_plugins

LOG_NAME = 'platform_installdeps' if __name__ == '__main__' else __name__
LOG = logging.getLogger(LOG_NAME)


def main():
    """
    Run all installers from the command line
    """
    loglevel = logging.WARNING
    if os.environ.get('INSTALLDEPS_DEBUG', 'false').lower() in ['true', '1', 'on']:
        loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel)

    # if os.path.exists(LEGACY_CONFIG_FILE):
    #     print('Legacy configuration file exists, using the legacy installer', flush=True)
    #     return legacy_main()

    config = Configuration().configuration
    installer_order = config.get('install', None)
    fail_on_error = config.get('fail_on_error', False)
    if not installer_order:
        installer_order = install_plugins.keys()

    for installer_name in installer_order:
        try:
            installer_class = install_plugins[installer_name]
        except KeyError:
            # No such installer class
            continue
        LOG.debug(f'Seeing if the {installer_name} tool is supported')
        installer_instance = installer_class()
        installer_instance.exit_on_missing = fail_on_error
        if not installer_instance.is_supported:
            continue
        if not installer_instance.has_dependencies:
            continue
        if installer_instance.plugin_configuration:
            print(f'Running {installer_name} installer ', flush=True)
            result = installer_instance.install_dependencies()
            if result:
                print(colored(f'Installed {len(result)} package{"s" if len(result) > 1 else ""}', 'green'), flush=True)
            else:
                print('No packages installed', flush=True)
            print('')


if __name__ == '__main__':
    sys.exit(main())
