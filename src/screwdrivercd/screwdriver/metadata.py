# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver metadata management functions
"""
import json
import logging
import subprocess#  # nosec


class Metadata(dict):
    """
    Screwdriver metadata wrapper

    all attributes to this class that are accessed or set will case the screwdriver meta command to run with the
    get or set for that specified value.

    Any underscore characters in the attribute name will be converted to period prior to getting/setting the value
    from screwdriver's metadata.
    """
    read_only = False

    def __getattr__(self, key):  # pragma: no cover
        """Get value from screwdriver metadata"""
        key = key.replace('_', '.')
        return self.get(key)

    def __setattr__(self, key, value):  # pragma: no cover
        """Set an attr to screwdriver metadata"""
        key = key.replace('_', '.')
        self.set(key, value)

    def get(self, key):  # pragma: no cover
        """
        Get a value from the screwdriver metadata store
        """
        command = ['meta', 'get', '--json-value', key]
        logging.debug(f'Running: {command}')
        try:
            response = subprocess.check_output(command).decode(errors='ignore')  # nosec
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        result = json.loads(response)
        return result

    def set(self, key, value):  # pragma: no cover
        """
        Set a value in the screwdriver metadata store
        """
        if self.read_only:
            logging.debug('Cannot write metadata, metadata is readonly')
            return
        command = ['meta', 'set', '--json-value', key, json.dumps(value)]
        logging.debug(f'Running: {command}')
        try:
            subprocess.check_call(command)  # nosec
        except (subprocess.CalledProcessError, FileNotFoundError):
            return
