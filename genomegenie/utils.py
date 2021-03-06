# coding=utf-8
"""Utilities"""

import re
from collections import deque, Sequence
from copy import deepcopy
from pathlib import Path
from ast import literal_eval

import pandas as pd
from glom import glom, Coalesce


def raise_if_not(items, obj, msg):
    for key in items:
        if key not in obj:
            raise ValueError(msg + f": {key}")


def consume(iterator):
    """Consume until exhausted

    see: "Itertools Recipes" in itertools docs
    """
    deque(iterator, maxlen=0)


class PrevItr(object):
    """Iterator that remembers the previous value.

    Iterating returns the current and the previous value.  The current and
    previous values are also accessible via the cur and prev properties of the
    iterator.

    """

    def __init__(self, itr):
        self.itr = itr
        self.prev = None
        self.cur = None

    def __next__(self):
        self.prev = self.cur
        self.cur = next(self.itr)
        return (self.prev, self.cur)

    def __iter__(self):
        return self


def flatten(lst):
    """Flatten an arbitrarily nested list"""
    for el in lst:
        if isinstance(el, Sequence) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def results(data, cols, depth=3):
    """Convert the returned job status from a pipeline to a dataframe

    Parameters
    ----------
    data : a doubly nested list of dictionaries

        An example of how data looks like: [[{}, {}], [[{}, {}], {}]].  The top
        two levels of nesting is mandatory, further nesting is handled by the
        `depth` argument.

    cols : iterable

        List of keys to extract from the data

    depth : int

        Maximum depth (defaults to 3) to search for the list of keys beyond the
        first two levels of nesting.

    Returns
    -------
    pandas.DataFrame

        a dataframe with `cols` as columns

    Examples
    --------
    >>> data = [
    ...     [{"a": 1, "b": 10}, {"a": 2, "b": 20}],
    ...     [[{"a": 3, "b": 30}, {"a": 4, "b": 40}], {"a": 5, "b": 50}],
    ... ]
    >>> results(data, ["a", "b"])
       a   b
    0  1  10
    1  2  20
    2  3  30
    3  4  40
    4  5  50

    """

    def _nest(key, depth):
        res = [key]
        for i in range(depth):
            res.append([res[-1]])
        return res

    return pd.DataFrame(
        dict(
            (
                key,
                [
                    i
                    for i in glom(
                        data, ([[Coalesce(*_nest(key, depth), default="?")]], flatten)
                    )
                ],
            )
            for key in cols
        )
    )


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


def contents(jobid, logdir):
    """Read log files for a given job id, and log directory

    This assumes the logfiles match the pattern '*.o<jobid>'.  It is also
    assumed that only a single file will match the pattern.

    Parameters
    ----------
    jobid : int or str
        A job id to match

    logdir : str
        Log directory as a relative or absolute path.  Note, that no checks are
        performed whether the path exists or not.

    Returns
    -------
    str
       Contents of the matched logfile as a string

    """
    matches = [i for i in Path(logdir).absolute().glob(f"*.o{jobid}")]
    assert 1 == len(matches)
    return matches[0].read_text()


def job_status(log):
    """Return job status by parsing log files

    At the end of the generated job scripts, a job status line is printed (see
    genomegenie/batch/templates/jobscript).  This function simply looks for
    this last line in any job output.

    Parameters
    ----------
    log : str
        Log contents as string

    Returns
    -------
    bool
        Job succeeded or not

    Examples
    --------
    >>> log = "\\n".join(["blabla"] * 3 + ["Pipeline job failed: 2334"])
    >>> job_status(log)
    False
    >>> log = "\\n".join(["blabla"] * 3 + ["Pipeline job finished: 2334"])
    >>> job_status(log)
    True

    """
    status = re.match("Pipeline job (failed|finished):.+", log.splitlines()[-1]).group(1)
    return status == "finished"


def read_config(filename):
    """Read pipeline config file

    Since the pipeline configuration makes use of both tuple, and list, a
    config file cannot be treated as a standard JSON file.  This function
    bypasses the issue by using ast.literal_eval(..) instead.

    >>> type(read_config("etc/pipeline-opts.py"))
    <class 'dict'>

    """
    return literal_eval(Path(filename).read_text())
