# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd exceptions
"""


class PackageError(object):
    """
    General package error
    """

class PackageValidationError(PackageError):
    """
    Validation of the package failed
    """


class PackageParseError(PackageValidationError):
    pass
