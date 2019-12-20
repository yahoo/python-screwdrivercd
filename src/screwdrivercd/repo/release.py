# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Source code repository management utilities
"""
import os
import subprocess  # nosec
import sys

from tempfile import TemporaryDirectory

from ..changelog.generate import changelog_contents
from ..utility.environment import env_bool


def create_release_tag(version: str, git_command: str='git', message: str=''):

    if not message:
        try:
            message = subprocess.check_output([git_command, 'log', '-n', '1']).decode(errors='ignore').split('\n')[4].strip()  # nosec
        except (subprocess.CalledProcessError, KeyError):
            message = f'New release {version}'

    with TemporaryDirectory() as tdir:
        tfilename = os.path.join(tdir, 'message')
        with open(tfilename, 'w') as fh:
            fh.write(message)
        command = [git_command, 'tag', '-a', f'v{version}', '-F', tfilename, '-f']
        subprocess.call(command)  # nosec


def push_release_tag(git_command: str='git', timeout=60):
    try:
        subprocess.check_call([git_command, 'push', '-f', '--tags'], timeout=timeout)  # nosec
    except subprocess.TimeoutExpired:
        print('\tTimeout occurred pushing tags to the remote', flush=True)
        return
    except subprocess.CalledProcessError:
        print('\tPush of git tag failed', flush=True)
    return


def main(meta_command: str='meta') -> int:

    if not env_bool('PUBLISH', True):
        print('Publish is disabled, skipping tag operation', flush=True)
        return 0

    if not env_bool('PACKAGE_TAG', True):
        print('Tagging is disabled for this job')
        return 0

    if not os.environ.get('GIT_DEPLOY_KEY', '') and not os.environ.get('SSH_AUTH_SOCK', ''):
        print('Git deployment key is not present, cannot commit tags to the git repo')
        return 0

    version = subprocess.check_output([meta_command, 'get', 'package.version']).decode(errors='ignore').strip()  # nosec
    if version == 'null':  # pragma: no cover
        print('No release version in metadata', flush=True)
        return 0

    print('# Creating tag', flush=True)
    create_release_tag(version=version)
    changelog = changelog_contents(f'v{version}').replace('\n#', '\n-')
    create_release_tag(version=version, message=changelog)

    print('\n# Pushing the tags', flush=True)
    push_release_tag()
    return 0


if __name__ == '__main__':
    sys.exit(main())
