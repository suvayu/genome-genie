import os
import pytest
import shlex
from time import sleep
from datetime import datetime
from itertools import product
from collections import namedtuple

import numpy as np
import dask
from dask.distributed import Client

from genomegenie.batch.jobs import Pipeline, results

from .test_batch_factory import _test_tmpl_dir_


@pytest.fixture(scope="module")
def pipeline_results():
    graph = [(["foo", "bar"], "baz"), "whaat"]

    def process(key):
        return [f"{key}-{i}" for i in range(2)] if key.startswith("b") else [f"{key}"]

    @dask.delayed
    def submit(job, monitor_t, *args):
        res = {"name": job, "beg": datetime.now()}
        sleep(3 * np.random.rand())
        res.update(end=datetime.now())
        return res

    client = Client()
    staged = Pipeline.stage(graph, process, submit)
    df = results(staged.compute(), 4, ["name", "beg", "end"])
    client.close()
    return df


def test_pipeline_stage_seq_dep(pipeline_results):
    df = pipeline_results
    foo = df.name.str.startswith("foo")
    bar = df.name.str.startswith("bar")
    baz = df.name.str.startswith("baz")
    wha = df.name.str.startswith("wha")

    # foo ends before bar starts
    t1 = df[foo].end
    t2 = df[bar].beg
    assert max(t1) < min(t2)

    # whaat starts after the last of foo, bar, and baz ends
    t1 = df[foo | bar | baz].end
    t2 = df[wha].beg
    assert max(t1) < min(t2)


@pytest.mark.skipif(
    condition=len(os.sched_getaffinity(0)) < 3,
    reason="Indeterminate in environments with very few threads",
)
def test_pipeline_stage_par(pipeline_results):
    df = pipeline_results
    foo = df.name.str.startswith("foo")
    bar = df.name.str.startswith("bar")
    baz = df.name.str.startswith("baz")

    # baz starts before foo or bar ends
    t1 = df[baz].beg
    t2 = df[foo | bar].end
    assert all(i > j for i, j in product(t2, t1))


def test_pipeline_process():
    opts = {
        "pipeline": [],
        "module": ["pkg1", "pkg2"],
        "inputs": [
            {"normal_bam": "normal1.bam", "tumor_bam": "tumor1.bam"},
            {"normal_bam": "normal2.bam", "tumor_bam": "tumor2.bam"},
            {"normal_bam": "normal3.bam", "tumor_bam": "tumor3.bam"},
        ],
        "test_all": {"inputs": "all", "normals_list": "normals.txt", "pon": "pon.vcf"},
        "test_regular": {
            "ref_fasta": "reference.fasta",
            "output": "result.vcf.gz",
            "db": "somedb.vcf",
            "pon": "pon.vcf",
            "nprocs": 4,
        },
        "test_override": {
            "inputs": [{"ajob": "result1.vcf.gz", "bjob": "result2.vcf.gz"}],
            "output": "consolidated.parquet",
        },
        "sge": {
            "queue": "short.q",
            "log_directory": "batch",
            "walltime": "00:30:00",
            "cputime": "00:30:00",
            "memory": "16 GB",
        },
    }

    pipeline = Pipeline(opts)  # sge with qsub
    pipeline.tmpl_dir = _test_tmpl_dir_

    # check number of jobs (varies with different input overrides)
    jobs = pipeline.process("test_all")
    assert 1 == len(jobs)

    jobs = pipeline.process("test_regular")
    assert len(jobs) == len(opts["inputs"])

    jobs = pipeline.process("test_override")
    assert len(jobs) == len(opts["test_override"]["inputs"])

    # task specific module override
    pipeline.options["test_regular"]["module"] = ["mypkg"]
    jobs = pipeline.process("test_regular")
    assert jobs[0].script.find("mypkg")
    assert all([i not in jobs[0].script for i in pipeline.options["module"]])


@pytest.mark.parametrize(
    "cmd, raise_on_err",
    [
        (shlex.split("ls /tmp"), True),
        pytest.param(
            shlex.split("ls /nonexistent"),
            True,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(shlex.split("ls /nonexistent"), False, marks=pytest.mark.xfail),
    ],
)
def test_pipeline_call(cmd, raise_on_err):
    out, err = Pipeline._call(cmd, raise_on_err)
    assert out
    assert not err
