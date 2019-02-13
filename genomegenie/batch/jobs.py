# coding=utf-8
"""Job splitting strategies

@author: Suvayu Ali
@date:   2018-12-20

"""


import logging
import shlex
import subprocess
import time
import re
import numpy as np
import pandas as pd
from uuid import uuid4
from collections.abc import Iterable
from contextlib import contextmanager
from functools import reduce
from textwrap import dedent
import pdb

import dask
from distributed.utils import parse_bytes, tmpfile
from glom import glom, Coalesce

from genomegenie.utils import add_class_property, flatten
from genomegenie.batch.factory import compile_template

# logger = logging.getLogger(__name__)


def results(res, depth=3, cols=["jobid", "out", "err", "script"]):
    """Convert the returned job status from a pipeline to a dataframe

    Please note this will work only for pipelines with a nesting level of 3 or
    less.  For pipelines with greater depth, you need to add an extra, more
    nested key as an argument to Coalesce below.

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
                        res, ([[Coalesce(*_nest(key, depth), default="?")]], flatten)
                    )
                ],
            )
            for key in cols
        )
    )


class Pipeline(object):
    """Data processing pipeline

    pipeline graph: [1, [2.1, 2.2], 3, [4.1, [4.2, 5.1]], 6, 7]

    """

    job_id_regexp = r"Your job (?P<job_id>\d+)"

    def __init__(self, cluster, options, backend="sge"):
        self.submit_command = cluster.submit_command
        self.graph = options["pipeline"]
        self.inputs = options["inputs"]
        self.options = options
        self.backend = backend

    def __repr__(self):
        res = f"""
        Pipeline: {self.graph}

        Backend: {self.backend}

        Inputs: {self.inputs}

        Options: {self.options}
        """
        return dedent(res)

    def _call(self, cmd, **kwargs):
        """Call a command using subprocess.Popen.

        (copied as is from JobQueueCluster, so that we can write a dummy
        cluster by inheriting from LocalCluster, useful for debugging)

        This centralizes calls out to the command line, providing consistent
        outputs, logging, and an opportunity to go asynchronous in the future.

        Parameters
        ----------
        cmd: List(str))
            A command, each of which is a list of strings to hand to
            subprocess.Popen

        Examples
        --------
        >>> self._call(['ls', '/foo'])

        Returns
        -------
        The stdout produced by the command, as string.

        Raises
        ------
        RuntimeError if the command exits with a non-zero exit code

        """
        cmd_str = " ".join(cmd)
        # logger.debug(
        #     "Executing the following command to command line\n{}".format(cmd_str)
        # )

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        out, err = proc.communicate()
        out, err = out.decode(), err.decode()
        if proc.returncode != 0:
            raise RuntimeError(
                "Command exited with non-zero exit code.\n"
                "Exit code: {}\n"
                "Command:\n{}\n"
                "stdout:\n{}\n"
                "stderr:\n{}\n".format(proc.returncode, cmd_str, out, err)
            )
        return (out, err)

    @classmethod
    def stage(self, graph, process=None, submit=None, monitor_t=600, *args):
        """Walk a pipeline graph and stage tasks.

        `graph` is the pipeline graph.

        `process` is a `Callable` used to generate the batch job templates
        (list of `BatchJob` instances) by applying on a graph element.  The
        generated job templates are then fed to the `Callable` `submit` which
        is wrapped by `dask.delayed`.  `args` are extra positional arguments
        that are passed on to submit.  Typically these are dummies used to
        enforce job dependencies; although nothing prevents a custom submit
        function to make use of these in other ways.

        The batch jobs are monitored every `monitor_t` seconds; passing 0 turns
        the monitoring off.  This is useful during testing, or when you know
        your pipeline is embarrassingly parallel (no dependent jobs).

        In the absence of `process` and `submit`, `Pipeline.process` and
        `Pipeline.submit` are used.

        """

        process = process if process is not None else self.process
        submit = submit if submit is not None else self.submit

        ## NOTE: remarks for the developer
        # stage(..) implements a recursive algorithm to walk the pipeline
        # graph.  The delayed job submission logic resides in the first
        # if-block, which is activated when the graph is a tuple.  Essentially
        # all elements are reduced to a tuple recursively, before this block
        # creates and submits the job.  It is easy to understand once you
        # realise an single entry (a string), is a 1-tuple (e.g. `("ajob",)`).
        # So the recursive logic simply splits by, list, tuple, or string,
        # until a graph element can be represented as a tuple of strings,
        # before creating a delayed job submission function and returning it.

        # set of parallel tasks:
        # e.g.: ("foo", "bar", "baz"), ("foo", "bar", ["baz1", "baz2"])
        if isinstance(graph, tuple):
            tasks = [
                [submit(job, monitor_t, *args) for job in process(task)]
                if isinstance(task, str)
                else self.stage(task, process, submit, monitor_t, *args)
                for task in graph
            ]
            return dask.delayed(tasks, nout=len(graph))
        # set of sequential tasks: may include nested set of parallel tasks
        # e.g.: ["foo1", "foo2", "foo3"], ["foo", ("bar1", "bar2"), "baz"]
        elif isinstance(graph, list):
            tasks = [
                self.stage(
                    (graph[0],) if isinstance(graph[0], str) else graph[0],
                    process,
                    submit,
                    monitor_t,
                    *args,
                )
            ]
            for task in graph[1:]:
                tasks.append(
                    self.stage(
                        (task,) if isinstance(task, str) else task,
                        process,
                        submit,
                        monitor_t,
                        tasks[-1],
                        *args,
                    )
                )
            return dask.delayed(tasks)
        else:
            raise TypeError(
                f"Unknown type in pipeline: {type(graph)}\n"
                "Allowed types: 'str', 'tuple', or 'list'"
            )

    def process(self, task):
        """Return list of jobs"""
        # NOTE: use dictionary unpacking to optionally overwrite global modules
        # with task specific modules
        opts = {
            "module": self.options["module"],
            **self.options[task],
            self.backend: self.options[self.backend],
        }
        if opts.get("inputs", None) == "ignore":
            jobs = [BatchJob(task, opts, self.backend)]
        elif opts.get("inputs", None) == "all":  # e.g. panel of normal
            keys = reduce(
                lambda i, j: i.union(set(j)), [i.keys() for i in self.inputs], set()
            )
            inputs = glom(
                self.inputs, dict((key, [Coalesce(key, default="")]) for key in keys)
            )
            for key in keys:  # filter out "no files" (shows as empty string above)
                inputs[key] = [i for i in filter(None, inputs[key])]
            jobs = [BatchJob(task, dict(**inputs, **opts), self.backend)]
        else:
            inputs = opts.get("inputs", self.inputs)  # allow overriding inputs per job
            jobs = [
                BatchJob(task, dict(**infile, **opts), self.backend)
                for infile in inputs
            ]
        return jobs

    @contextmanager
    def job_file(self, script):
        """ Write job submission script to a temporary file

        script -- script contents

        """
        with tmpfile(extension="sh") as fn:
            with open(fn, "w") as f:
                # logger.debug(f"writing job script: {fn}\n{script}")
                f.write(script)
            yield fn

    @dask.delayed
    def submit(self, job, monitor_t, *args):
        """Submit and wait"""
        res = dict(script=job.script)
        with self.job_file(job.script) as fn:
            res["out"], res["err"] = self._call(shlex.split(self.submit_command) + [fn])
            res["jobid"] = self._job_id_from_submit_output(res["out"])
            err = False
            while monitor_t and not err:  # not err => running
                out, err = self._call(shlex.split(f"qstat -j {res['jobid']}"))
                time.sleep(monitor_t)
        return res

    def _job_id_from_submit_output(self, out):
        """(copied as is from JobQueueCluster)"""
        match = re.search(self.job_id_regexp, out)
        if match is None:
            msg = (
                "Could not parse job id from submission command "
                "output.\nJob id regexp is {!r}\nSubmission command "
                "output is:\n{}".format(self.job_id_regexp, out)
            )
            raise ValueError(msg)

        job_id = match.groupdict().get("job_id")
        if job_id is None:
            msg = (
                "You need to use a 'job_id' named group in your regexp, e.g. "
                "r'(?P<job_id>\d+)', in your regexp. Your regexp was: "
                "{!r}".format(self.job_id_regexp)
            )
            raise ValueError(msg)

        return job_id


add_class_property(Pipeline, "graph")
add_class_property(Pipeline, "options")


class BatchJob(object):
    """Wrapper to generate, submit, and manage batch jobs.

    template -- command template ("mytemplate" from above example)

    options -- dict: keys are templates, values are options
               Typically options are dictionaries, except for "module".

               {
                   "module": ["foo", "bar", "baz"],
                   "mytemplate": {"key1": "val1", "key2": "val2", "nprocs": 4},
                   "sge": {
                       "queue": "name",
                       "log_directory": "dirname",
                       "walltime": "runtime estimate",
                       "cputime": "per proc cputime estimate",
                       "memory": "total memory requirement",
                   },
               }

               time spec: hh:mm:ss
               memory spec: 100MB, 4 GB, etc

    backend  -- batch system template

    """

    def __init__(self, template, options, backend="sge"):
        # pdb.set_trace()
        self._template = template  # for __repr__
        self.setup = compile_template("module", package=" ".join(options["module"]))
        self.job_cmd = compile_template(template, **options)
        jobopts = options[backend]
        jobopts["memory"] = "{}".format(parse_bytes(jobopts["memory"]))
        jobopts["name"] = f"{template}-{uuid4()}"
        # TODO: check walltime and cputime format
        # TODO: check if queue is valid
        self.job_header = compile_template(backend, **jobopts)
        self.script = compile_template(
            "jobscript",
            job_header=self.job_header,
            setup=self.setup,
            job_cmd=self.job_cmd,
        )

    def __repr__(self):
        res = f"""
        BatchJob({self._template}) at {id(self)}

        Script:
        {self.script}
        """
        return dedent(res)
