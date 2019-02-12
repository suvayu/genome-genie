from time import sleep
from datetime import datetime
from itertools import product
from warnings import filterwarnings

import numpy as np
import dask
from dask.distributed import Client

from genomegenie.batch.jobs import Pipeline, results


filterwarnings(action="ignore", category=UserWarning, message=".*")


def test_pipeline_stage():
    graph = [(["foo", "bar"], "baz"), "whaat"]

    def process(key):
        return [f"{key}-{i}" for i in range(2)] if key.startswith("b") else [f"{key}"]

    @dask.delayed
    def submit(job, monitor_t, *args):
        res = {"name": job, "beg": datetime.now()}
        sleep(3*np.random.rand())
        res.update(end=datetime.now())
        return res

    client = Client()
    staged = Pipeline.stage(graph, process, submit)
    df = results(staged.compute(), 4, ["name", "beg", "end"])

    foo = df.name.str.startswith("foo")
    bar = df.name.str.startswith("bar")
    baz = df.name.str.startswith("baz")
    wha = df.name.str.startswith("wha")

    # foo ends before bar starts
    t1 = df[foo].end
    t2 = df[bar].beg
    assert max(t1) < min(t2)

    # baz starts before foo or bar ends
    t1 = df[baz].beg
    t2 = df[foo | bar].end
    assert all(i > j for i, j in product(t2, t1))

    # whaat starts after the last of foo, bar, and baz ends
    t1 = df[foo | bar | baz].end
    t2 = df[wha].beg
    assert max(t1) < min(t2)


opts = {
    "pipeline": [(["prep1", "ajob"], "bjob"), "finalize"],
    "module": ["pkg1", "pkg2"],
    "inputs": [
        {"normal_bam": "normal1.bam", "tumor_bam": "tumor1.bam"},
        {"normal_bam": "normal2.bam", "tumor_bam": "tumor2.bam"},
        {"normal_bam": "normal3.bam", "tumor_bam": "tumor3.bam"},
    ],
    "split": {},
    "prep1": {"ref_fasta": "reference.fasta", "db": "somedb.vcf", "pon": "pon.vcf"},
    "ajob": {
        "ref_fasta": "reference.fasta",
        "output": "result1.vcf.gz",
        "db": "somedb.vcf",
        "pon": "pon.vcf",
        "nprocs": 4,
    },
    "bjob": {
        "ref_fasta": "reference.fasta",
        "output": "result2.vcf.gz",
        "db": "somedb.vcf",
        "nprocs": 4,
    },
    "finalize": {
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

# if __name__ == '__main__':
#     cluster = DummyCluster(processes=True)
#     client = Client(cluster)
#     res = test_pipeline_stage()


