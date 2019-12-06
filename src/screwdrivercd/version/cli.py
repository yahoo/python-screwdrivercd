# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""Functions for command script"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig,  update_job_status
logging_basicConfig(check_prefix='VERSION')

import logging
import sys
from .arguments import parse_arguments
from .setup import setupcfg_has_metadata
from .version_types import versioners


LOG_NAME = 'platform_version' if __name__ == '__main__' else __name__
LOG = logging.getLogger(LOG_NAME)


def main():
    """Run the tool from the command line"""
    args = parse_arguments()

    if args.force_update or setupcfg_has_metadata():
        versioner = versioners[args.version_type]
        print(f'Updating version using the {versioner.name} version plugin', flush=True)
        version = versioner(ignore_meta_version=args.ignore_meta, update_sdv4_meta=args.update_meta)

        version.update_setup_cfg_metadata()
        if args.update_meta:
            version.update_meta_version()
            update_job_status(status='SUCCESS', message=f'version=={version}')
            print(f'Version in setup.cfg and screwdriver v4 metadata package.version updated to: {version}', flush=True)
        else:
            print(f'Version in setup.cfg updated to: {version}')
    else:
        print("The 'setup.cfg' file does not have a metadata section with a version in it, not modifying it", file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()
