# coding=utf-8
"""Utilities"""


from collections import deque
from copy import deepcopy


def raise_if_not(items, obj, msg):
    for key in items:
        if key not in obj:
            raise ValueError(msg + f": {key}")


def consume(iterator):
    """Consume until exhausted

    see: "Itertools Recipes" in itertools docs
    """
    deque(iterator, maxlen=0)


def add_class_property(cls, prop):
    """Dynamically add a property and a setter that does deepcopy.

    Note: a deleter is not defined, so if your property needs special care to
    delete, please do not use this helper function.

    """

    def _getter(self):
        return getattr(self, f"_{prop}", None)

    def _setter(self, val):
        setattr(self, f"_{prop}", deepcopy(val))

    _prop = property(_getter, _setter, None, f"Property {prop}")
    setattr(cls, prop, _prop)
