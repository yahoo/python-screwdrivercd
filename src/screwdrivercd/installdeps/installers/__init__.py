# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Package installer classes
"""
from .apk import ApkInstaller
from .apt import AptInstaller
from .brew import BrewInstaller
from .pip3 import PipInstaller
from .yum import YumInstaller


__all__ = ['apk', 'apt', 'brew', 'pip3', 'yum']
install_plugins = {
    'apk': ApkInstaller,
    'apt-get': AptInstaller,
    'brew': BrewInstaller,
    'pip3': PipInstaller,
    'yum': YumInstaller
}
