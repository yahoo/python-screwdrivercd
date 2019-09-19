import copy
import unittest
import os
import subprocess
import sys
import tempfile


from screwdrivercd.screwdriver.metadata import Metadata


class ScrewdriverTestCase(unittest.TestCase):
    """
    Test case class for testing screwdriver wrappers that perform common operations like saving/restoring the environment
    variables for each test.
    """
    cwd = None
    orig_argv = None
    orig_environ =None
    tempdir = None
    environ_keys = {
        'BASE_PYTHON', 'PACKAGE_DIR', 'PACKAGE_DIRECTORY', 'SD_ARTIFACTS_DIR', 'SD_BUILD', 'SD_BUILD_ID',
        'SD_PULL_REQUEST',
    }
    meta_version = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Save the original sys.argv, working directory and environment variable values so they can be modified
        # freely in the tests and restored after each test.
        self.orig_argv = sys.argv
        self.cwd = os.getcwd()
        self.orig_environ = copy.copy(os.environ)

        # Save the value of the "package.version" from the screwdriver pipeline metadata if it is present
        try:
            self.meta_version = subprocess.check_output(['meta', 'get', 'package.version']).decode(errors='ignore').strip()  # nosec
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    def setUp(self):
        Metadata.read_only = True

        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)

        # Delete keys in the environ keys so they aren't set
        self.delkeys(self.environ_keys)

        # Create expected CI directories
        self.artifacts_dir = os.path.join(self.tempdir.name, 'artifacts')
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.environ['SD_ARTIFACTS_DIR'] = self.artifacts_dir

        # Make sure the value of SD_PULL_REQUEST is always unset
        os.environ['SD_PULL_REQUEST'] = ''


    def tearDown(self):
        Metadata.read_only = False

        # Restore sys.argv
        if self.orig_argv:
            sys.argv = self.orig_argv

        # Return to the original working directory
        if self.cwd:
            os.chdir(self.cwd)

        # Clean up the temporary directory
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

        # Reset the environment variables to the original values
        for environ_key in self.environ_keys:
            environ_value = self.orig_environ.get(environ_key, None)
            if environ_value:
                os.environ[environ_key] = self.orig_environ[environ_key]
            elif environ_value is None and environ_key in os.environ.keys():
                del os.environ['environ_key']

        # Restore the package.version if it was saved
        if self.meta_version and self.meta_version != 'null':  # Make sure meta_version gets set back
            try:
                subprocess.check_call(['meta', 'set', 'package.version', self.meta_version])  # nosec
            except FileNotFoundError:
                pass

    def delkeys(self, keys):
        """
        Delete keys from the environment

        Parameters
        ----------
        keys: list
            The environment keys to remove
        """
        for key in keys:
            try:
                del os.environ[key]
            except KeyError:
                pass

    def write_config_files(self, config_files):
        for filename, contents in config_files.items():
            dirname = os.path.dirname(filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(filename, 'wb') as fh:
                fh.write(contents)

    def setupEmptyGit(self):
        """
        Set up an empty git repo, in the current directory
        """
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'config', 'user.email', 'foo@bar.com'])
        subprocess.check_call(['git', 'config', 'user.name', 'foo'])
        with open('setup.cfg', 'w') as setup_handle:
            setup_handle.write('')
        subprocess.check_call(['git', 'add', 'setup.cfg'])
        subprocess.check_call(['git', 'commit', '-a', '-m', 'initial'])
