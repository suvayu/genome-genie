#!/bin/env python3

import os.path
import time

import pyarrow as pa
import pyarrow.parquet as pq

from pysam import VariantFile

from genomegenie.schemas import get_vcf_cols
from genomegenie.io import get_header, to_arrow

# data files: {20..22},X,Y
data_t = 'data/ALL.chr{}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz'
data_x = 'data/ALL.chrX.phase3_shapeit2_mvncall_integrated_v1b.20130502.genotypes.vcf.gz'
data_y = 'data/ALL.chrY.phase3_integrated_v1b.20130502.genotypes.vcf.gz'

chrom = 20
vf = VariantFile(data_t.format(chrom), mode='r', threads=4)
hdr, samples = get_header(vf)

# if not os.path.exists('data/pq/header.pq'):
#     hdr.to_parquet('data/pq/header.pq')

# # data
# data_t = pa.union([
#     pa.field('i', pa.int32()),
#     pa.field('f', pa.float32())
# ], 'dense')

cols = get_vcf_cols(hdr)
schema = pa.schema(cols)
struct = pa.struct(cols)

# # debug:
# vf_itr = vf.fetch(f"{chrom}", 0, 70_000, reopen=True)
# for i, r in enumerate(vf_itr):
#     if i > 102: break           # go to 64139: ALT: A,T

t0 = time.process_time()
batches = [to_arrow(vf.fetch("20", i*500_000, (i + 1)*500_000, reopen=True), cols)
           for i in range(32)]
t1 = time.process_time()
tbl = pa.Table.from_batches(batches, schema)
