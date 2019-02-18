import pytest

from genomegenie.batch.factory import compile_template


@pytest.mark.skip(reason="Test not implemented")
def test_sge():
    pass


@pytest.mark.skip(reason="Test not implemented")
def test_module():
    pass


@pytest.mark.skip(reason="Test not implemented")
def test_pon_sample():
    opts = {
        "ref_fasta": "foo.fa",
        "normal_bam": "/input/normal1.bam",
        "output": "/output",
        "db": "genomedb.vcf.gz",
        "exome_bed": "exome.bed",
    }


@pytest.mark.skip(reason="Test not implemented")
def test_pon_consolidate():
    opts = {
        "normals_list": "/output/normals.txt",
        "normal_bam": ["/input/normal1.bam", "/input/normal2.bam"],
        "output": "/output",
        "pon": "/output/pon.vcf.gz",
    }


@pytest.mark.skip(reason="Test not implemented")
def test_gatk():
    opts = {
        "ref_fasta": "foo.fa",
        "normal_bam": "/input/normal1.bam",
        "tumor_bam": "/input/tumor1.bam",
        "output": "/output",
        "db": "genomedb.vcf.gz",
        "pon": "pon.vcf.gz",
        "exome_bed": "exome.bed",
        "nprocs": 4,
    }


@pytest.mark.skip(reason="Test not implemented")
def test_muse():
    opts = {
        "ref_fasta": "foo.fa",
        "normal_bam": "/input/normal1.bam",
        "tumor_bam": "/input/tumor1.bam",
        "output": "/output",
        "db": "genomedb.vcf.gz",
        "exome_bed": "exome.bed",
    }


@pytest.mark.skip(reason="Test not implemented")
def test_freebayes():
    pass


@pytest.mark.skip(reason="Test not implemented")
def test_strelka():
    pass


@pytest.mark.skip(reason="Test not implemented")
def test_jobscript():
    pass
