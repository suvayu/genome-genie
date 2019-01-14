# coding=utf-8
"""Filters for Mako templates"""


from functools import partial


def sample_name(filename):
    # FIXME: just a place holder
    return f"{filename}_name"


def filename_filter(fname, ext1, ext2):
    """Convert filenames of one type to another (used in templates)"""
    return fname[: fname.rfind(ext1)] + ext2


vcf2tsv = partial(filename_filter, ext1="vcf", ext2="tsv")
vcf2bam = partial(filename_filter, ext1="vcf", ext2="bam")
ungz = partial(filename_filter, ext1=".gz", ext2="")
gz = partial(filename_filter, ext1="", ext2=".gz")
