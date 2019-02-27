from pathlib import Path
import logging

from dask.distributed import Client, LocalCluster

from genomegenie.batch.jobs import Pipeline
from genomegenie.utils import results


datadir = Path("/packages/suvayu-testing")
inputs = Path("inputs")
outputs = Path("outputs")
gatk_dir = outputs / Path("gatk")
muse_dir = outputs / Path("muse")

bam_t = ("normal_bam", "tumor_bam")
bams = [
    (Path("RADS18B_mergeFiltered.bam"), Path("RADS18D_mergeFiltered.bam")),
    (Path("RADS4B_mergeFiltered.bam"), Path("RADS4D_mergeFiltered.bam")),
]

ref = Path("refseq/NCBI37_WO_DECOY.fa")
dbsnp = Path("dbsnp/dbsnp_138.hg19.vcf.gz")
genomedb = Path("genomedb/af-only-gnomad.raw.sites.b37.vcf.gz")
normals = Path("normals.txt")
pon = Path("pon.vcf.gz")
exome_bed = Path("exome_bed/TruSeq_exome_targeted_regions.hg19.bed")

opts = {
    "pipeline": (["pon_sample", "pon_consolidate", "gatk"], "muse"), # "variants"
    "module": ["samtools-1.9", "gatk-4.0.4.0", "MuSE-1.0"],
    "inputs": [
        dict((i, str(datadir / inputs / j)) for i, j in zip(bam_t, bam)) for bam in bams
    ],
    "pon_sample": {
        "ref_fasta": str(datadir / ref),
        "output": str(datadir / gatk_dir),
        "db": str(datadir / genomedb),
        "exome_bed": str(datadir / exome_bed),
        "nprocs": 4,
    },
    "pon_consolidate": {
        "inputs": "all",
        "normals_list": str(datadir / gatk_dir / normals),
        "output": str(datadir / gatk_dir),
        "db": str(datadir / genomedb),
        "pon": str(datadir / gatk_dir / pon),
        "nprocs": 4,
    },
    "gatk": {
        "ref_fasta": str(datadir / ref),
        "output": str(datadir / gatk_dir),
        "db": str(datadir / genomedb),
        "pon": str(datadir / gatk_dir / pon),
        "exome_bed": str(datadir / exome_bed),
        "nprocs": 4,
    },
    "muse": {
        "ref_fasta": str(datadir / ref),
        "output": str(datadir / muse_dir),
        "db": str(datadir / dbsnp),
        "exome_bed": str(datadir / exome_bed),
    },
    "variants": {
        "inputs": [{"gatk": str(datadir / gatk_dir), "muse": str(datadir / muse_dir)}]
    },
    "sge": {
        "queue": "all.q",
        "log_directory": "pipeline",
        "walltime": "24:00:00",
        "cputime": "06:00:00",
        "memory": "32 GB",
    },
}


if __name__ == "__main__":
    logger = logging.getLogger("genomegenie")
    handler = logging.StreamHandler()
    fmt = "{levelname}:{asctime}:{name}:{lineno}: {message}"
    formatter = logging.Formatter(fmt, style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    cluster = LocalCluster(n_workers=4, processes=True, memory_limit="1GB")
    client = Client(cluster)

    pipeline = Pipeline(opts)
    staged = pipeline.stage(
        pipeline.graph, pipeline.process, pipeline.submit, monitor_t=3600
    )
    res = staged.compute()
    df = results(res, cols=["jobid", "out", "err", "script"])
    df.to_parquet("pipeline-output.parquet")
