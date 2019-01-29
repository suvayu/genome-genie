# coding=utf-8
"""Job splitting strategies

@author: Suvayu Ali
@date:   2018-12-20

"""


import logging
import shlex
import time
import numpy as np
from collections.abc import Iterable
from contextlib import contextmanager
from functools import reduce
import pdb

import dask
from distributed.utils import parse_bytes, tmpfile
from glom import glom, Coalesce

from genomegenie.utils import add_class_property
from genomegenie.batch.factory import compile_template

# logger = logging.getLogger(__name__)


class Pipeline(object):
    """Data processing pipeline

    pipeline graph: [1, [2.1, 2.2], 3, [4.1, [4.2, 5.1]], 6, 7]

    """

    def __init__(self, cluster, options, backend="sge"):
        self.submit_command = cluster.submit_command
        self.graph = options["pipeline"]
        self.inputs = options["inputs"]
        self.options = options
        self.backend = backend  # FIXME: propagate down the chain

    def __repr__(self):
        pass

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
        logger.debug(
            "Executing the following command to command line\n{}".format(cmd_str)
        )

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
        return out

    def walk(self, graph, predicate):
        """Walk a pipeline graph and apply predicate"""
        if not isinstance(graph, str) and isinstance(graph, Iterable):
            return [self.walk(item, predicate) for item in graph]
        else:
            return predicate(graph)

    # @dask.delayed
    def process(self, task):
        """Return future"""
        # FIXME: propagate backend
        # NOTE: use dictionary unpacking to optionally overwrite global modules
        # with task specific modules
        opts = {
            "module": self.options["module"],
            **self.options[task],
            self.backend: self.options[self.backend],
        }
        if opts.get("inputs", None) == "ignore":
            jobs = [BatchJob(task, opts)]
        elif opts.get("inputs", None) == "all":  # e.g. panel of normal
            keys = reduce(
                lambda i, j: i.union(set(j)), [i.keys() for i in self.inputs], set()
            )
            inputs = glom(
                self.inputs, dict((key, [Coalesce(key, default="")]) for key in keys)
            )
            for key in keys:
                inputs[key] = [i for i in filter(None, files[key])]
            jobs = [BatchJob(task, dict(**inputs, **opts))]
        else:
            jobs = [BatchJob(task, dict(**infile, **opts)) for infile in self.inputs]
        return [self.submit(job) for job in jobs]

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

    # @dask.delayed
    def submit(self, job):
        with self.job_file(job.script) as fn:
            out = self._call(shlex.split(self.submit_command) + [fn])
            time.sleep(np.random.randint(2, 10))
            return out


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
        pdb.set_trace()
        self.setup = compile_template("module", package=" ".join(options["module"]))
        self.job_cmd = compile_template(template, **options)
        jobopts = options[backend]
        jobopts["memory"] = "{}".format(parse_bytes(jobopts["memory"]))
        # FIXME: do this in pipeline
        # if "log_directory" not in jobopts:
        #     jobopts["log_directory"] = self.cluster.log_directory
        # TODO: check walltime and cputime format
        # TODO: check if queue is valid
        self.job_header = compile_template(backend, **jobopts)
        self.script = compile_template(
            "jobscript",
            job_header=self.job_header,
            setup=self.setup,
            job_cmd=self.job_cmd,
        )