{
    "pipeline": (
        [
            "pon_sample",
            "pon_consolidate",
            "gatk"
        ],
        "muse"
    ),
    "module": [
        "samtools-1.9",
        "gatk-4.0.4.0",
        "MuSE-1.0"
    ],
    "inputdir": "/packages/suvayu-testing/inputs",
    "inputs": [
        {
            "normal_bam": "RADS18B_mergeFiltered.bam",
            "tumor_bam": "RADS18D_mergeFiltered.bam"
        },
        {
            "normal_bam": "RADS4B_mergeFiltered.bam",
            "tumor_bam": "RADS4D_mergeFiltered.bam"
        }
    ],
    "pon_sample": {
        "ref_fasta": "/packages/suvayu-testing/refseq/NCBI37_WO_DECOY.fa",
        "output": "/packages/suvayu-testing/outputs/gatk",
        "db": "/packages/suvayu-testing/genomedb/af-only-gnomad.raw.sites.b37.vcf.gz",
        "exome_bed": "/packages/suvayu-testing/exome_bed/TruSeq_exome_targeted_regions.hg19.bed",
        "nprocs": 4
    },
    "pon_consolidate": {
        "inputs": "all",
        "normals_list": "/packages/suvayu-testing/outputs/gatk/normals.txt",
        "output": "/packages/suvayu-testing/outputs/gatk",
        "db": "/packages/suvayu-testing/genomedb/af-only-gnomad.raw.sites.b37.vcf.gz",
        "pon": "/packages/suvayu-testing/outputs/gatk/pon.vcf.gz"
    },
    "gatk": {
        "ref_fasta": "/packages/suvayu-testing/refseq/NCBI37_WO_DECOY.fa",
        "output": "/packages/suvayu-testing/outputs/gatk",
        "db": "/packages/suvayu-testing/genomedb/af-only-gnomad.raw.sites.b37.vcf.gz",
        "pon": "/packages/suvayu-testing/outputs/gatk/pon.vcf.gz",
        "exome_bed": "/packages/suvayu-testing/exome_bed/TruSeq_exome_targeted_regions.hg19.bed",
        "nprocs": 4
    },
    "muse": {
        "ref_fasta": "/packages/suvayu-testing/refseq/NCBI37_WO_DECOY.fa",
        "output": "/packages/suvayu-testing/outputs/muse",
        "db": "/packages/suvayu-testing/dbsnp/dbsnp_138.hg19.vcf.gz",
        "exome_bed": "/packages/suvayu-testing/exome_bed/TruSeq_exome_targeted_regions.hg19.bed"
    },
    "variants": {
        "inputs": [
            {
                "gatk": "/packages/suvayu-testing/outputs/gatk",
                "muse": "/packages/suvayu-testing/outputs/muse"
            }
        ]
    },
    "sge": {
        "queue": "all.q",
        "log_directory": "pipeline",
        "walltime": "24:00:00",
        "cputime": "06:00:00",
        "memory": "32 GB"
    }
}
