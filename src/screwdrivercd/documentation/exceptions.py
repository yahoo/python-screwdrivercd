# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
screwdrivercd.documentation module command exceptions
"""
class DocBuildError(Exception):
    """Generic Documentation Generation Error"""
    plugin: str=''


class DocPublishError(Exception):
    """Documentation Publication Error"""
    plugin: str=''
