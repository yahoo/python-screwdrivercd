# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd.changelog module entrypoint
"""
import sys
from .generate import main


sys.exit(main())
