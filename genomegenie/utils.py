# coding=utf-8
"""Utilities"""


def raise_if_not(items, obj, msg):
    for key in items:
        if key not in obj:
            raise ValueError(msg + f": {key}")
