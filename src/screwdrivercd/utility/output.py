# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Screwdriver Utility Output helpers
"""
import logging
import os
import shutil
import sys
import textwrap

from termcolor import colored

LOG = logging.getLogger(__name__)



def header(text='', width=None, separator=None, outfile=None, collapse=False):
    """
    Display a textual header message.

    Parameters
    ----------
    text : str
        The text to print/display
    width : int, optional
        The width (text wrap) of the header message.
        This will be the current terminal width as determined
        by the 'stty size' shell command if not specified.
    separator : str, optional
        The character or string to use as a horizontal
        separator.  Will use '=' if one is not specified.
    outfile : File, optional
        The File object to print the header text to.
        This will use sys.stdout if not specified.
    :return:
    """
    if not outfile:
        outfile = sys.stdout

    width = width or shutil.get_terminal_size().columns

    separator = separator or '='

    # Screwdriver buffers stdout and stderr separately.  This can
    # cause output from previous operations to show after our
    # header text.  So we flush the output streams to ensure
    # all existing output is sent/displayed before printing our
    # header.
    sys.stderr.flush()
    outfile.flush()

    if collapse:
        for line in textwrap.wrap(text, width=width-4):
            header_line = separator + ' ' + line + ' ' + separator * (width - 4 - len(line))
            print(header_line, file=outfile)
    else:
        # Print the header text
        horiz = separator * width
        print(horiz, file=outfile)
        print(
            os.linesep.join(textwrap.wrap(text, width=width)),
            file=outfile
        )
        print(horiz, file=outfile)

    # Once again flush our header to the output stream so things
    # show up in the correct order.
    sys.stderr.flush()
    outfile.flush()


def status_message(message: str='', indent: int=0, color: str=''):
    """
    Format a message as an error message

    Parameters
    ----------
    message: str
        The error message

    indent: int
        How far to indent the message

    color: str, optional
        The color to make the message

    Returns
    -------
    str:
        The formatted message
    """
    outstring = textwrap.indent(message, prefix=' ' * indent)
    if color:
        outstring = colored(outstring, color=color)
    return outstring


def print_error(message: str='', indent: int=0, file=sys.stdout):
    """
    Print an error message in color

    Parameters
    ----------
    message: str
        The message to display
    indent: int, optional
        Number of columns to indent, default=0
    file: file
        File type object to send the output to
    """
    print(status_message(message, indent=indent, color='red'), file=file, flush=True)
