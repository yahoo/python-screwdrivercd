# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Python packaging command line wrapper
"""
import sys
from .build_python import main


if __name__ == '__main__':
    sys.exit(main())
