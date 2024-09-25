# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd version module
"""
from typing import List
from importlib.metadata import version, PackageNotFoundError


__all__: List[str] = ['arguments', 'cli', 'exceptions', 'setup', 'version_types']
__copyright__: str = "Copyright 2019, Oath Inc."

__version__: str = "0.0.0"
try:  # pragma: no cover
    __version__ = version("screwdrivercd")
except PackageNotFoundError:
    pass
