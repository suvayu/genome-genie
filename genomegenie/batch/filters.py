# coding=utf-8
"""Filters to be used in Mako templates"""


import inspect
import logging
import re as _re
import shlex as _shlex
import subprocess as _subprocess
from functools import partial as _partial
from pathlib import Path as _Path

from jinja2 import Undefined


logger = logging.getLogger(__name__)


def path_transform(fname, destdir, ext=None):
    """Rename a file path to a different directory.

    Given a filename, and a destination directory, return a new path that
    "moves" the file to the destination directory.  Optionally, if an extension
    is provided, the extension of the filename is also transformed.

    >>> path_transform('/path/to/input/sample.bam', '/path/to/output')
    '/path/to/output/sample.bam'
    >>> path_transform('/path/to/input/sample.bam', '/path/to/output', 'vcf')
    '/path/to/output/sample.vcf'

    """
    try:
        fname, destdir = _Path(fname), _Path(destdir)
    except TypeError as err:
        logger.error(
            f"Undefined argument to {inspect.stack()[0].function}: "
            f"{repr(fname)}, {repr(destdir)}\n{err}"
        )
        # # alternate implementation: pass on undefined to the next step
        # for i in [fname, destdir]:
        #     if isinstance(i, Undefined):
        #         return i
        return ""

    if ext is None or isinstance(ext, Undefined):
        res = destdir / fname.name
        if isinstance(ext, Undefined):
            logger.warning(
                f"Ignoring undefined argument to "
                f"{inspect.stack()[0].function}: 'ext'"
            )
    else:
        res = destdir / (fname.stem + f".{ext}")

    return str(res)


def filename_filter(fname, ext1, ext2):
    """Convert filenames of one type to another.

    NOTE: If you need to do a non-trivial replacement, you should include the
    preceding '.' to anchor your pattern (see examples below)

    >>> filename_filter('sample.bam', 'bam', 'vcf')
    'sample.vcf'
    >>> filename_filter('variants.vcf.gz', '.gz', '')
    'variants.vcf'
    >>> filename_filter('variants.vcf', '', '.gz')
    'variants.vcf.gz'
    >>> filename_filter('sample.bam', '.bam', '-pon.vcf.gz')
    'sample-pon.vcf.gz'

    """
    try:
        return fname[: fname.rfind(ext1)] + ext2
    except TypeError as err:
        logger.error(
            f"Undefined argument to {inspect.stack()[0].function}: "
            f"{repr(fname)}, {repr(ext1)}, {repr(ext2)}"
        )
        return ""


vcf2tsv = _partial(filename_filter, ext1="vcf", ext2="tsv")
vcf2bam = _partial(filename_filter, ext1="vcf", ext2="bam")
ungz = _partial(filename_filter, ext1=".gz", ext2="")
gz = _partial(filename_filter, ext1="", ext2=".gz")
bam2pon = _partial(filename_filter, ext1=".bam", ext2="-pon.vcf.gz")
bam2tsv = _partial(filename_filter, ext1="bam", ext2="tsv")
bam2vcf = _partial(filename_filter, ext1="bam", ext2="vcf")
