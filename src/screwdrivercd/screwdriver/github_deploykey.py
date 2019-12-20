# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver github deploy key setup utility
"""
# The logging_basicConfig has to be run before other imports because some modules we use log output on import
# pylint: disable=wrong-import-order, wrong-import-position
from ..screwdriver.environment import logging_basicConfig
logging_basicConfig(check_prefix='GIT_DEPLOYKEY')

import base64
import distro
import logging
import os
import shutil
import subprocess  # nosec
import tempfile
from hashlib import sha256
from urllib.parse import urlparse

from ..installdeps.cli import main as installdeps_main
from ..utility.contextmanagers import InTemporaryDirectory

logger = logging.getLogger(__name__)


fingerprints = {
    'old github fingerprint': b'16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48',     # Old github fingerprint, For openssh < 7.4
    'new github_fingerprint': b'SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8',  # New github fingerprint for openssh >= 7.4
}


ssh_agent_deploy_conf = """[build-system]
# Minimum requirements for the build system to execute.
requires = ["setuptools", "wheel"]  # PEP 508 specifications.

[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'yum']

    [tool.sdv4_installdeps.apk]
        deps = ['openssh-client']
    
    [tool.sdv4_installdeps.apt-get]
        deps = ['openssh-client']
    
    [tool.sdv4_installdeps.yum]
        deps = ['openssh-clients']
"""


def git_key_secret() -> bytes:
    git_key = os.environ.get('GIT_DEPLOY_KEY', '')
    if not git_key:  # Nothing to do
        return b''

    git_key_decoded = base64.b64decode(git_key)
    if not git_key_decoded.startswith(b'-----BEGIN RSA PRIVATE KEY-----\n'):
        print('Decoded GIT_DEPLOY_KEY secret does not have a private key header')
    if not git_key_decoded.endswith(b'-----END RSA PRIVATE KEY-----\n'):
        print('Decoded GIT_DEPLOY_KEY secret does not have a private key footer')
    return git_key_decoded


def add_github_to_known_hosts(known_hosts_filename: str = '~/.ssh/known-hosts'):  # pragma: no cover
    """
    Add the github hosts to the known hosts

    Parameters
    ----------
    known_hosts_filename: str, optional
        The known_hosts file to update
    """
    known_hosts_filename = os.path.expanduser(known_hosts_filename)
    known_hosts_dirname = os.path.dirname(known_hosts_filename)
    os.makedirs(os.path.expanduser(known_hosts_dirname), exist_ok=True, mode=0o0700)
    os.chmod(os.path.dirname(known_hosts_filename), 0o0700)

    keyscan_command = shutil.which('ssh-keyscan')
    if not keyscan_command:
        keyscan_command = '/usr/bin/ssh-keyscan'

    with open(known_hosts_filename, 'ab') as fh:
        os.fchmod(fh.fileno(), 0o0600)
        fh.write(b'\n')
        subprocess.check_call([keyscan_command, 'github.com'], stdout=fh)  # nosec


def validate_known_good_hosts(known_hosts_filename: str = '~/.ssh/known-hosts') -> bool:  # pragma: no cover
    """
    Check the known hosts for the github hosts

    Returns
    -------
    bool
        True if at least one good host is present, False otherwise
    """
    known_hosts_filename = os.path.expanduser(known_hosts_filename)

    match = False
    output = subprocess.check_output(['ssh-keygen', '-l', '-f', known_hosts_filename])  # nosec
    for desc, fingerprint in fingerprints.items():
        if fingerprint not in output:
            print(f'Known github fingerprint {desc} is missing from known-hossts')
            continue
        match = True
    return match


def load_github_key(git_key):  # pragma: no cover
    """
    Load the github key into the ssh-agent
    """
    # subprocess.run(['ssh-add'], input=git_key)  # nosec
    # return
    git_key_passphrase = os.environ.get('GIT_DEPLOY_KEY_PASSPHRASE', '')
    with tempfile.TemporaryDirectory() as tempdir:
        os.makedirs(os.path.join(tempdir, '.ssh'), mode=0o0700)
        key_filename = os.path.join(tempdir, '.ssh/git_key')
        m = sha256()
        m.update(git_key)
        print(f'Private key hash: {m.hexdigest()}')
        with open(key_filename, 'wb') as fh:
            os.fchmod(fh.fileno(), 0o0600)
            fh.write(git_key)
        with open(f'{key_filename}.pub', 'wb') as fh:
            os.fchmod(fh.fileno(), 0o0644)
            command = ['ssh-keygen', '-vv', '-y', '-f', key_filename]
            command += ['-P', git_key_passphrase]
            subprocess.check_call(command, stdout=fh, timeout=15)  # nosec
        subprocess.check_call(['ssh-add', key_filename], stdin=subprocess.DEVNULL, timeout=15)  # nosec


def set_git_mail_config():  # pragma: no cover
    """
    Set the git mail config variables
    """
    subprocess.check_call(['git', 'config', '--global', 'user.email', "dev-null@screwdriver.cd"])  # nosec
    subprocess.check_call(['git', 'config', '--global', 'user.name', "sd-buildbot"])  # nosec


def update_git_remote():  # pragma: no cover
    """
    Update the git remote address to use the git protocol via ssh
    """
    new_git_url = None
    remote_output = subprocess.check_output(['git', 'remote', '-v'])  # nosec
    remote_output = remote_output.decode(errors='ignore')
    for line in remote_output.split('\n'):
        line = line.strip()
        splitline = line.split()
        if len(splitline) != 3:
            continue
        remote, old_git_url, remote_type = splitline
        if remote != 'origin':
            continue
        if remote_type != '(push)':
            continue
        if 'http' not in old_git_url:
            continue
        parsed_url = urlparse(old_git_url)
        new_git_url = f'git@{parsed_url.netloc}:{parsed_url.path.lstrip("/")}'
        break
    if new_git_url:
        subprocess.check_call(['git', 'remote', 'set-url', '--push', 'origin', new_git_url])  # nosec
        subprocess.check_call(['git', 'remote', 'set-url', 'origin', new_git_url])  # nosec
        subprocess.call(['git', 'remote', '-v'])  # nosec


def install_ssh_agent():  # pragma: no cover
    """
    Install ssh-agent if it is missing
    """
    missing = False
    for command in ['ssh-agent', 'ssh-keyscan']:
        if not shutil.which(command):  # Already installed
            missing = True
            break

    if not missing:
        return

    print('# Installing openssh client', flush=True)
    with InTemporaryDirectory():
        with open('pyproject.toml', 'w') as fh:
            fh.write(ssh_agent_deploy_conf)
        installdeps_main()


def setup_ssh_main() -> int:  # pragma: no cover
    """
    Github deploykey ssh setup, setup ssh eiddcchttjfenrtetcgbiglgcgfureejrluufcbjbngj
    so that ssh-agent can be startedx.

    Returns
    -------
    int:
        The returncode to be returned from the utility
    """
    git_key = git_key_secret()
    if not git_key:  # Nothing to do
        print('No GIT_DEPLOY_KEY secret present')
        return 0

    logger.debug('Installing ssh clients if it is not installed')
    install_ssh_agent()

    print('\n# Adding github.com to known_hosts')
    add_github_to_known_hosts()

    # The validation below does not work with the version of ssh-keygen on centos 5
    # so on that operating system we skip the validation.
    if distro.id() in ['rhel']:
        if distro.major_version() in ['5']:
            return 0

    print('\n# Validating known good hosts')
    validate_known_good_hosts()

    return 0


def add_deploykey_main() -> int:  # pragma: no cover
    """
    Github deploykey setup utility, this utility adds the keys from the screwdriver secrets into the ssh-agent.

    This tool requires that ssh-agent be running already.

    Returns
    -------
    int:
        The returncode to be returned from the utility
    """
    git_key = git_key_secret()
    if not git_key:  # Nothing to do
        return 0

    print('\n# Loading the github key into the ssh-agent')
    load_github_key(git_key)

    print('\n# Setting the git user.email and user.name config settings')
    set_git_mail_config()

    print('\n# Updating the git remote to use the ssh url')
    update_git_remote()

    add_github_to_known_hosts('/root/.ssh/known_hosts')

    return 0
