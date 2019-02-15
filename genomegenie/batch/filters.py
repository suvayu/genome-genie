# coding=utf-8
"""Filters to be used in Mako templates"""


import re
import shlex
import subprocess
from functools import partial
from pathlib import Path


def sample_name(filename, cmd_t="", debug=False):
    """Read the sample name from a BAM file using samtools"""
    if debug:
        return f"{filename}_name"

    # collect samtools output
    cmd_t = cmd_t if cmd_t else f"samtools view -H {filename}"
    res = subprocess.check_output(
        shlex.split(cmd_t)
    ).splitlines()
    # match something like this:
    # @RG  ID:Sample_01130111_BC2ULEACXX_L4  PL:Illumina  PU:C2ULEACXX.4  LB:01130111  SM:Sample_01130111
    anchor, sep, group = "^@RG", "\t", "([^\t]+)"
    pattern = re.compile(sep.join([anchor] + [group] * 4 + [":".join([group] * 2)]))
    for line in res:
        found = pattern.search(line.decode("utf-8"))
        if found:  # match the first by convention
            break
    return found.group(6)


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
    fname, destdir = Path(fname), Path(destdir)
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


vcf2tsv = partial(filename_filter, ext1="vcf", ext2="tsv")
vcf2bam = partial(filename_filter, ext1="vcf", ext2="bam")
ungz = partial(filename_filter, ext1=".gz", ext2="")
gz = partial(filename_filter, ext1="", ext2=".gz")
bam2pon = partial(filename_filter, ext1=".bam", ext2="-pon.vcf.gz")
