# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Documentation generator plugin classes
"""
import hashlib
import importlib.metadata
import logging
import os
import subprocess  # nosec - All subprocess calls use full path
import sys
import tempfile

from typing import List

from termcolor import colored

from .exceptions import DocBuildError, DocPublishError
from .utility import clean_directory, copy_contents
from ..changelog.generate import write_changelog
from ..utility.environment import interpreter_bin_command, standard_directories


logger = logging.getLogger(__name__)


class DocumentationPlugin:
    """
    screwdrivercd.documentation generation/publication plugin
    """
    name: str = 'base'
    build_command: List[str] = [interpreter_bin_command(), '-c', 'print("building")']
    build_log_filename: str = ''
    build_output_dir = ''
    build_dest: str = ''
    publish_branch: str = 'gh-pages'
    publish_log_filename: str = ''
    git_command_timeout: int = 300
    _clone_dir = ''
    _clone_url = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        directories = standard_directories('documentation')
        self.interpreter_bin_dir = os.path.dirname(sys.executable)
        self.build_dir = os.path.abspath(directories['documentation'])
        self.log_dir = os.path.abspath(directories['logs'])
        self.build_log_filename = os.path.join(self.log_dir, f'{self.name}.build.log')
        self.publish_log_filename = os.path.join(self.log_dir, f'{self.name}.publish.log')
        self.build_dest = os.path.join(self.build_dir, self.build_output_dir)
        self.source_dir = os.getcwd()
        try:
            self.git_command_timeout = int(os.environ.get("DOCUMENTATION_GIT_TIMEOUT", str(self.git_command_timeout)))
        except ValueError:
            logger.warning('Value {os.environ.get("DOCUMENTATION_GIT_TIMEOUT", str(self.git_command_timeout))} for the DOCUMENTATION_GIT_TIMEOUT setting is invalid')

    @property
    def clone_dir(self) -> str:
        """
        Determine the git clone url for the current repo

        Returns
        -------
        str:
            Clone url, will be an empty string if it cannot be found
        """
        if not self._clone_dir:  # pragma: no cover
            self._clone_dir = self.get_clone_dir()
        return self._clone_dir

    @property
    def clone_url(self) -> str:
        """
        Determine the git clone url for the current repo

        Returns
        -------
        str:
            Clone url, will be an empty string if it cannot be found
        """
        if not self._clone_url:  # pragma: no cover
            self._clone_url = self.get_clone_url()
        return self._clone_url

    @property
    def documentation_is_present(self) -> bool:  # pragma: no cover
        """
        Returns
        =======
        bool:
            Check that the documentation source is present, Returns True if it is, False otherwise
        """
        return False

    @staticmethod
    def get_sha1_hashes(directory_path, remove_git=True):
        sha1_hashes = {}

        for root, _, files in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, directory_path)

                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha1()
                        while chunk := f.read(8192):
                            file_hash.update(chunk)
                        sha1_hashes[relative_path] = file_hash.hexdigest()
                elif os.path.islink(file_path):  # pragma: no cover
                    sha1_hashes[relative_path] = hashlib.sha1(relative_path.encode(errors='ignore')).hexdigest()
        if remove_git:
            remove_keys = []
            for key in sha1_hashes.keys():
                if key == '.git' or key.startswith('.git/'):
                    remove_keys.append(key)
            for key in remove_keys:
                del sha1_hashes[key]
        return sha1_hashes

    @staticmethod
    def diff_dictionaries(dict1, dict2):
        diff = {
            'added': {},
            'removed': {},
            'changed': {}
        }

        for key in dict1:
            if key not in dict2:
                diff['removed'][key] = dict1[key]
            elif dict1[key] != dict2[key]:
                diff['changed'][key] = {'from': dict1[key], 'to': dict2[key]}

        for key in dict2:
            if key not in dict1:
                diff['added'][key] = dict2[key]

        return diff

    def _run_command(self, command: List, log_filename: str, timeout: int = 0):
        """

        Parameters
        ----------
        command: List
            Parsed command to run

        log_filename: str
            Filename to write the log entry to
        """
        log_dir = os.path.dirname(log_filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        logger.debug(f'Running command {command!r}, logging to {log_filename!r}')
        error_message = None
        with open(log_filename, 'ab') as log_file:
            try:
                if timeout:  # pragma: no cover
                    subprocess.check_call(command, stdout=log_file, stderr=subprocess.STDOUT, timeout=timeout)  # nosec - All subprocess calls use full path
                else:
                    subprocess.check_call(command, stdout=log_file, stderr=subprocess.STDOUT)  # nosec - All subprocess calls use full path
            except (FileNotFoundError, subprocess.CalledProcessError,) as error:
                error_message = f'Command {" ".join(self.build_command)!r} failed {error}'
            except subprocess.TimeoutExpired as error:  # pragma: no cover
                error_message = f'Command {" ".join(self.build_command)!r} timeout after {timeout} seconds {error}'
        if error_message:
            raise DocBuildError(error_message)

    def _log_message(self, message: str, log_filename: str = '', end: str = '\n'):
        if not log_filename:
            log_filename = self.build_log_filename
        log_dir = os.path.dirname(log_filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(log_filename, 'ab') as log_file:
            log_file.write(message.encode())
            if end:
                log_file.write(end.encode())

    def remove_build_log(self):
        """Remove the build log"""
        if os.path.exists(self.build_log_filename):
            os.remove(self.build_log_filename)

    def remove_publish_log(self):
        """Remove the publish log"""
        if os.path.exists(self.publish_log_filename):
            os.remove(self.publish_log_filename)

    def clean_directory(self, directory_name: str):
        """
        Clean out the specified directory

        Parameters
        ----------
        directory_name : str
            Directory to empty
        """
        self._log_message(f'\n- Cleaning out the old document contents', self.publish_log_filename)
        clean_directory(directory_name=directory_name)

    def copy_contents(self, src: str, dest: str):
        """
        Copy the contents of the source directory to the destination directory

        Parameters
        ----------
        src: str
            The source directory

        dest: str
            The destination directory
        """
        self._log_message(f'\n- In Directory {os.getcwd()} Copying files from {src} -> {dest}', self.publish_log_filename)
        copy_contents(src, dest)

    def clone_documentation_branch(self):  # pragma: no cover
        """
        Clone and checkout the current documentation branch
        """
        self._log_message(f'\n- Cloning the {self.publish_branch!r} of the {self.clone_url!r} repo', self.publish_log_filename)
        if os.path.isdir(self.publish_log_filename):
            os.remove(self.publish_log_filename)

        with open(self.publish_log_filename, 'ab') as log_file:
            try:
                subprocess.check_call(['git', 'clone', self.clone_url, '--branch', self.publish_branch], stdout=log_file, stderr=subprocess.STDOUT)  # nosec - All subprocess calls use full path
            except subprocess.CalledProcessError as error:
                subprocess.check_call(['git', 'clone', self.clone_url], stdout=log_file, stderr=subprocess.STDOUT)  # nosec - All subprocess calls use full path
                os.chdir(self.clone_dir)
                subprocess.check_call(['git', 'checkout', '-b', self.publish_branch], stdout=log_file, stderr=subprocess.STDOUT)  # nosec - All subprocess calls use full path
                os.chdir('..')
            if not os.path.exists(self.clone_dir):
                raise DocPublishError(f"Repo directory {self.clone_dir} is missing after git clone")

    def get_clone_url(self) -> str:
        """
        Determine the git clone url for the current git repo

        Returns
        -------
        str:
            The git url of the current repo
        """
        self._log_message('\n- Getting the clone url', self.publish_log_filename)
        cwd = os.getcwd()
        os.chdir(self.source_dir)
        try:
            output = subprocess.check_output(['git', 'remote', 'show', 'origin'], stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path
        except subprocess.CalledProcessError:  # pragma: no cover
            os.chdir(cwd)
            return ''
        for line in output.decode(errors='ignore').split(os.linesep):
            line = line.strip()
            if line.startswith('Fetch URL:'):
                os.chdir(cwd)
                return ':'.join(line.split(':')[1:]).strip()
        os.chdir(cwd)  # pragma: no cover
        return ''  # pragma: no cover

    def get_clone_dir(self) -> str:
        """
        Return the name of the directory that will be created when git clone runs

        Returns
        -------
        str
            git clone directory
        """
        result = os.path.abspath(self.get_clone_url().split('/')[-1].removesuffix('.git'))
        self._log_message(f'Determining the clone directory {result}', self.publish_log_filename)
        return result

    def git_add_all(self):
        """
        Run 'git add' on all the files in the current directory.
        """
        subprocess.run(['git', 'config', 'advice.addIgnoredFile', 'false'], stderr=subprocess.DEVNULL)  # nosec - All subprocess calls use full path

        self._log_message('\n- Adding all files in the current directory to git', self.publish_log_filename)
        for filename in os.listdir('.'):
            if filename in ['.git', '.gitignore'] or filename.startswith('.git/'):
                continue
            logger.debug('Adding %s to git', filename)
            self._run_command(['git', 'add', filename], log_filename=self.publish_log_filename)
        logger.debug('Done adding files')

    def git_commit_documentation(self, message: str = 'Update documentation'):  # pragma: no cover
        """
        Run git commit on all files in the current repo

        Parameters
        ----------
        message: str, optional
            The commit message to use
        """
        self._log_message('\n- Committing git changes', self.publish_log_filename)
        self._run_command(['git', 'commit', '-a', '-m', message], log_filename=self.publish_log_filename)

    def git_push_documentation(self):  # pragma: no cover
        """
        Push the current repository
        """
        self._log_message(f'\n- Pushing the documentation to the {self.publish_branch} branch', self.publish_log_filename)
        self._run_command(['git', 'push', 'origin', self.publish_branch], log_filename=self.publish_log_filename, timeout=self.git_command_timeout)

    def disable_jekyll(self):
        """
        Disable github's jekyll processing for the current repo
        """
        self._log_message('\n- Writing the .nojekyll file to disable github jekyll processing', self.publish_log_filename)
        disable_file = open('.nojekyll', 'w')
        disable_file.close()
        self._run_command(['git', 'add', '.nojekyll'], log_filename=self.publish_log_filename)

    def build_setup(self):
        """
        Run operations to setup the build
        """

    def build_cleanup(self):
        """
        Run operations to cleanup after the build
        """

    def build_documentation(self) -> str:
        """
        Build the documentation with the documentation build tool

        Raises
        ------
        DocBuildError:
            The documentation generate command returned an error

        Returns
        -------
        str:
            The root directory of the generated documenation
        """
        self._log_message(f'\n- Building the {self.name} format documentation', self.build_log_filename)

        self.build_setup()

        cwd = os.getcwd()
        os.chdir(self.source_dir)
        os.makedirs(self.build_dest, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # self.remove_build_log()

        try:
            self._run_command(self.build_command, log_filename=self.build_log_filename)
        finally:
            os.chdir(cwd)

        self.build_cleanup()
        return self.build_dest

    def publish_documentation(self, clear_before_build=True, push=True):  # pragma: no cover
        """
        Build and publish the documentation

        Raises
        ------
        DocumentationBuildError:
            If the build operation failed

        DocumentationPublishError:
            Publish to the destination failed
        """
        self._log_message(f'\n- Publishing the documentation to github pages', self.publish_log_filename)
        self.remove_publish_log()

        # Build the documentation
        build_dest = self.build_documentation()

        if not push:
            return

        # Make sure there is a clone url before trying to publish
        if not self.clone_url:  # pragma: no cover
            raise DocPublishError('Unable to determine a valid git clone url to publish to')

        # Checkout the documentation branch into a temporary directory, add the docs and commit them
        with tempfile.TemporaryDirectory() as tempdir:    # pragma: no cover
            os.chdir(tempdir)
            self.clone_documentation_branch()
            self.original_hashes = self.get_sha1_hashes(self.clone_dir)
            if clear_before_build:
                self.clean_directory(self.clone_dir)
            self.copy_contents(build_dest, self.clone_dir)

            os.chdir(self.clone_dir)
            self.disable_jekyll()
            self.updated_hashes = self.get_sha1_hashes(self.clone_dir)

            if self.original_hashes == self.updated_hashes:
                self._log_message('No changes to the documentation to publish', self.publish_log_filename)
            else:
                self._log_message(f'Changed files {self.diff_dictionaries(self.original_hashes, self.updated_hashes)}', self.publish_log_filename)
                self.git_add_all()
                self.git_commit_documentation()
                self.git_push_documentation()

        os.chdir(self.source_dir)


def documentation_plugins(documentation_formats=None):
    """
    Get documentation plugin instances
    """
    for entry_point in importlib.metadata.entry_points(group='screwdrivercd.documentation.plugin'):
        try:
            instance = entry_point.load()()
        except Exception as e:  # pragma: no cover
            logger.warning(f'Documentation plugin {entry_point} failed to load due to a package dependency conflict: {e}')
            raise
        if documentation_formats and instance.name not in documentation_formats:
            continue
        yield instance


def generate_changelog():
    """
    Generate a changelog if the CHANGELOG_FILENAME is set
    """
    changelog_filename = os.environ.get('CHANGELOG_FILENAME', '')
    if not changelog_filename:
        return

    write_changelog(changelog_filename)


def build_documentation(documentation_formats=None):
    """
    Generate documentation using all plugins that can generate documentation
    """
    failed = []
    generate_changelog()
    for documentation_plugin in documentation_plugins(documentation_formats=documentation_formats):
        if documentation_plugin.documentation_is_present:

            print(f'Building {documentation_plugin.name!r} documentation: ', end='', flush=True)
            try:
                documentation_plugin.build_documentation()
                print(colored('Ok', color='green'), flush=True)
            except DocBuildError as error:
                print(colored('Failed', color='red'), flush=True)
                logger.error(f'Building {documentation_plugin.name!r} documentation {colored("Failed", color="red")}')
                if documentation_plugin.build_log_filename and os.path.exists(documentation_plugin.build_log_filename):  # pragma: no cover
                    with open(documentation_plugin.build_log_filename, 'r') as build_log:
                        if logger.level <= logging.DEBUG:
                            logger.error(f'{documentation_plugin.name} build Failed {str(error)}')
                            logger.error(build_log.read())
                        else:
                            print(build_log.read(), flush=True)
                else:  # pragma: no cover
                    logger.debug('No output from the build command was logged')
                failed.append(documentation_plugin.name)

            if documentation_plugin.build_log_filename and os.path.exists(documentation_plugin.build_log_filename):  # pragma: no cover
                with open(documentation_plugin.build_log_filename, 'r') as build_log:
                    logger.debug(f'{documentation_plugin.name} build output')
                    logger.debug(build_log.read())

            if failed:
                raise DocBuildError(f'Documentation build failed for: {" ".join(failed)}')


def publish_documentation(documentation_formats=None, push: bool=True):  # pragma: no cover
    """
    Publish documentation using all plugins that can generate documentation
    """
    clear_before_build = True
    failed = []
    generate_changelog()
    for documentation_plugin in documentation_plugins(documentation_formats=documentation_formats):
        if documentation_plugin.documentation_is_present:
            print(f'Publishing {documentation_plugin.name!r} documentation: ', end='', flush=True)
            try:
                documentation_plugin.publish_documentation(clear_before_build=clear_before_build, push=push)
                print(colored('Ok', color='green'), flush=True)
            except (DocBuildError, DocPublishError) as error:
                print(colored('Failed', color='red'), flush=True)
                if documentation_plugin.build_log_filename and os.path.exists(documentation_plugin.build_log_filename):
                    with open(documentation_plugin.build_log_filename, 'r') as build_log:
                        logger.error(f'{documentation_plugin.name} build Failed {str(error)}')
                        logger.error(build_log.read())
                if documentation_plugin.publish_log_filename and os.path.exists(documentation_plugin.publish_log_filename):
                    with open(documentation_plugin.publish_log_filename, 'r') as publish_log:
                        logger.error(f'{documentation_plugin.name} publish failed {str(error)}')
                        logger.error(publish_log.read())
                error.plugin = documentation_plugin
                failed.append(documentation_plugin.name)
            clear_before_build = False

            if documentation_plugin.build_log_filename and os.path.exists(documentation_plugin.build_log_filename):
                with open(documentation_plugin.build_log_filename, 'r') as build_log:
                    logger.debug(f'{documentation_plugin.name} build output')
                    logger.debug(build_log.read())

            if documentation_plugin.publish_log_filename and os.path.exists(documentation_plugin.publish_log_filename):
                with open(documentation_plugin.publish_log_filename, 'r') as publish_log:
                    logger.debug(f'{documentation_plugin.name} publish output')
                    logger.debug(publish_log.read())

            if failed:
                raise DocPublishError(f'Documentation publish failed for: {" ".join(failed)}')
