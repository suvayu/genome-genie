# coding=utf-8
"""CLI utilities"""


import logging
from argparse import ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter


class RawArgDefaultFormatter(
    ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
):
    """Combine raw help text formatting with default argument display."""

    pass


def logger_config(logger, fmt, loglevel, filename=None):
    formatter = logging.Formatter(fmt, style="{")
    logstream = logging.StreamHandler()
    logstream.setFormatter(formatter)
    logger.addHandler(logstream)
    if filename:
        logfile = logging.FileHandler(filename)
        logfile.setFormatter(formatter)
        logger.addHandler(logfile)
    logger.setLevel(loglevel)
    return logger
