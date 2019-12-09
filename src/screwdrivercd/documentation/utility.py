# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Documentation Utility functions
"""
import logging
import os
import shutil


logger = logging.getLogger(__name__)  # pylint: disable=C0103


def clean_directory(directory_name):
    """
    Remove all files and folders from a directory that do not begin with '.'

    Parameters
    ----------

    directory_name : str
        Directory to be cleaned up.
    """
    for filename in os.listdir(directory_name):
        if filename.startswith('.'):  # pragma: no cover
            continue
        full_filename = os.path.join(directory_name, filename)
        logger.debug('Removing file: %s', full_filename)
        if os.path.isdir(full_filename):
            shutil.rmtree(full_filename)
        else:
            os.remove(full_filename)


def copy_contents(src, dest, skip_dotfiles=False):
    """
    Copy the contents of the src directory to the dest directory

    Parameters
    ----------

    src : str
        Source directory

    dest : str
        Destination directory

    skip_dotfiles : bool
        Don't copy dotfiles if True.
    """
    logger.debug('Copying: %s -> %s', src, dest)
    cwd = os.getcwd()
    dest = os.path.abspath(dest)
    os.chdir(src)

    for dirname, subdirlist, filelist in os.walk('.'):  # pylint: disable=W0612
        logger.debug('Found directory: %s', dirname)
        if dirname.startswith('./'):  # pragma: no cover
            dirname = dirname[2:]
        destdir = os.path.join(dest, dirname)
        logger.debug('Dest directory: %s', destdir)
        os.makedirs(destdir, exist_ok=True)
        for fname in filelist:
            if skip_dotfiles and fname.startswith('.'):
                continue
            srcfile = os.path.join(dirname, fname)
            destfile = os.path.join(destdir, fname)
            logger.debug('\tcopying file: %s -> %s', srcfile, destfile)
            shutil.copyfile(srcfile, destfile)
    os.chdir(cwd)
