# coding=utf-8
"""Job splitting strategies

@author: Suvayu Ali
@date:   2018-12-20

"""

from abc import ABC, abstractmethod


class BatchJob(ABC):
    def __init__(self, cluster):
        # job_header abd partly the env comes from cluster,
        # cmd specific env and cmd depends on the specific job
        self.job_header = cluster.job_header
        # fallback to env_header from `JobQueueCluster`
        self.env_header = getattr(cluster, "env_header", cluster._env_header)
        self.script_template = cluster._script_template

    @property
    def setup_cmds(self):
        return self._setup_cmds

    @setup_cmds.setter
    def setup_cmds(self, setup_cmds):
        self._setup_cmds = setup_cmds

    @property
    def job_cmd(self):
        return self._job_cmd

    @job_cmd.setter
    @abstractmethod
    def job_cmd(self, cmd_with_opts):
        # FIXME: probably want to ingest a dict
        self._job_cmd = cmd_with_opts

    @property
    def job_script(self):
        pieces = {
            "job_header": self.job_header,
            "env_header": self.env_header,
            "worker_command": "\n".join(self.setup_cmds + self.job_cmd),
        }
        return self.script_template % pieces


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
