# coding=utf-8
"""Job splitting strategies

@author: Suvayu Ali
@date:   2018-12-20

"""


from string import Template
from textwrap import dedent

from distributed.utils import parse_bytes

from genomegenie.utils import add_class_property
from genomegenie.batch.factory import command


class Pipeline(object):
    pass


class BatchJob(object):
    """Wrapper to generate, submit, and manage batch jobs.

    cluster -- JobQueueCluster instance

    resources -- dict: with resource requirements

                 


    options -- dict: keys are templates, values are options
               Typically options are dictionaries, except for "module".

               >>> {
                   'module': ['foo', 'bar', 'baz'],
                   'mytemplate': {'key1': 'val1', 'key2': 'val2', 'nprocs': 4},
                   'sge': {'queue': 'name', 'log_directory': 'dirname',
                           'walltime': 'runtime estimate',
                           'cputime': 'per proc cputime estimate',
                           'memory': 'total memory requirement'}
               }

               time spec: hh:mm:ss
               memory spec: 100MB, 4 GB, etc

    """

    _script_template = Template(
        dedent(
            """
    #!/bin/bash

    # job options
    $job_header

    # setup
    $setup

    # job command
    $job_cmd
    """
        )
    )

    def __init__(self, cluster, options, template, batch_system="sge"):
        self.cluster = cluster
        self.setup = command("module", package=" ".join(options["module"]))
        self.job_cmd = command(template, **options[template])
        jobopts = options[batch_system]
        jobopts["memory"] = "{}".format(parse_bytes(jobopts["memory"]))
        if "log_directory" not in jobopts:
            jobopts["log_directory"] = self.cluster.log_directory
        # TODO: check walltime and cputime format
        # TODO: check if queue is valid
        self.job_header = command(batch_system, **jobopts)

    @property
    def setup(self):
        return self._setup

    @setup.setter
    def setup(self, setup):
        self._setup = setup

    @property
    def job_cmd(self):
        return self._job_cmd

    @job_cmd.setter
    def job_cmd(self, cmd_with_opts):
        self._job_cmd = cmd_with_opts

    @property
    def job_script(self):
        return self._script_template.safe_substitute(
            job_header=self.job_header, setup=self.setup, job_cmd=self.job_cmd
        )


# Variant Caller inputs:
# - [Germline, Somatic] reference (fasta)
# - [Germline, Somatic] normal (bam)
# - [Somatic] tumour (bam)
# - [Somatic] bed (optional, region boundary)
# - [Joint] bams
class VariantCall(BatchJob):
    pass


class Split(BatchJob):
    """Split datasets to process in parallell

    criteria:
    - sample
    - chromosome

    """

    pass


class QueryCmd(object):
    """Query datasets to read metadata"""

    pass
