from pprint import pprint

from dask.distributed import Client

from glom import glom, Coalesce, Inspect

from genomegenie.utils import flatten
from genomegenie.batch.debug import DummyCluster
from genomegenie.batch.jobs import Pipeline, results
from genomegenie.batch.factory import compile_template

opts = {
    "pipeline": ["pon_sample", "pon_consolidate", "gatk"],
    "module": ["gatk-4.0.1", "samtools"],
    "inputs": [
        {"normal_bam": "normal1.bam", "tumor_bam": "tumor1.bam"},
        {"normal_bam": "normal2.bam", "tumor_bam": "tumor2.bam"},
        {"normal_bam": "normal3.bam", "tumor_bam": "tumor3.bam"},
    ],
    "gatk": {
        "ref_fasta": "reference.fasta",
        "output": "result.vcf.gz",
        "db": "somedb.vcf",
        "pon": "pon.vcf",
        "nprocs": 4,
    },
    "pon_sample": {"ref_fasta": "reference.fasta", "db": "somedb.vcf"},
    "pon_consolidate": {"inputs": "all", "normals_list": "foo.txt", "pon": "pon.vcf"},
    "sge": {
        "name": "faketest",
        "queue": "short.q",
        "log_directory": "batch",
        "walltime": "00:30:00",
        "cputime": "00:30:00",
        "memory": "16 GB",
    },
}

dummyopts = {
    # "pipeline": ["prep1", "ajob", "finalize"],
    "pipeline": [(["prep1", "ajob"], "bjob"), "finalize"],
    "module": ["gatk-4.0.1", "samtools"],
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


if __name__ == '__main__':
    cluster = DummyCluster(processes=True)
    client = Client(cluster)
    pipeline = Pipeline(cluster, dummyopts)
    staged = pipeline.stage(pipeline.graph, monitor_t=0)
    res = staged.compute()

    df = results(res)
    df.info()
    df.to_csv('job_output.csv')
