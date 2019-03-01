# coding=utf-8
"""Filters to be used in Mako templates"""


import re as _re
import shlex as _shlex
import subprocess as _subprocess
from functools import partial as _partial
from pathlib import Path as _Path


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
    fname, destdir = _Path(fname), _Path(destdir)
    if ext is None:
        res = destdir / fname.name
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
    return fname[: fname.rfind(ext1)] + ext2


vcf2tsv = _partial(filename_filter, ext1="vcf", ext2="tsv")
vcf2bam = _partial(filename_filter, ext1="vcf", ext2="bam")
ungz = _partial(filename_filter, ext1=".gz", ext2="")
gz = _partial(filename_filter, ext1="", ext2=".gz")
bam2pon = _partial(filename_filter, ext1=".bam", ext2="-pon.vcf.gz")
bam2tsv = _partial(filename_filter, ext1="bam", ext2="tsv")
bam2vcf = _partial(filename_filter, ext1="bam", ext2="vcf")
