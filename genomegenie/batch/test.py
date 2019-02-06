from dask.distributed import Client

from glom import glom

from genomegenie.batch.debug import DummyCluster
from genomegenie.batch.jobs import Pipeline
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

# cluster = DummyCluster(processes=True)
# client = Client(cluster)

# pipeline = Pipeline(cluster, opts)
# staged = pipeline.walk(pipeline.graph, pipeline.process)

dummyopts = {
    "pipeline": ["prep1", "ajob"],
    "module": ["gatk-4.0.1", "samtools"],
    "inputs": [
        {"normal_bam": "normal1.bam", "tumor_bam": "tumor1.bam"},
        {"normal_bam": "normal2.bam", "tumor_bam": "tumor2.bam"},
        {"normal_bam": "normal3.bam", "tumor_bam": "tumor3.bam"},
    ],
    "ajob": {
        "ref_fasta": "reference.fasta",
        "output": "result.vcf.gz",
        "db": "somedb.vcf",
        "pon": "pon.vcf",
        "nprocs": 4,
    },
    "prep1": {"ref_fasta": "reference.fasta", "db": "somedb.vcf", "pon": "pon.vcf"},
    "sge": {
        "queue": "short.q",
        "log_directory": "batch",
        "walltime": "00:30:00",
        "cputime": "00:30:00",
        "memory": "16 GB",
    },
}
