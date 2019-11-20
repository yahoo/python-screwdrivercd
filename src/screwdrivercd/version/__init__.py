# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd version module
"""
from typing import List
import pkg_resources


__all__: List[str] = ['arguments', 'cli', 'exceptions', 'setup', 'version_types']
__copyright__: str = "Copyright 2019, Oath Inc."
__version__: str = pkg_resources.get_distribution("screwdrivercd").version
