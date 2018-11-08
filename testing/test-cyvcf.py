#!/bin/env python3

from collections import defaultdict

import pyarrow as pa
import pyarrow.parquet as pq

from cyvcf2.cyvcf2 import VCF

# data files: {20..22},X,Y
data_t = 'data/ALL.chr{}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz'
data_x = 'data/ALL.chrX.phase3_shapeit2_mvncall_integrated_v1b.20130502.genotypes.vcf.gz'
data_y = 'data/ALL.chrY.phase3_integrated_v1b.20130502.genotypes.vcf.gz'

chrom = 20
achrom = VCF(data_t.format(chrom))

header = [i for i in achrom.header_iter()]

hdrstats = defaultdict(int)
for hdr in header:
    for key in hdr.info().keys():
        hdrstats[key] += 1

# extract headers
struct_t = pa.struct([
    ('HeaderType', pa.string()),
    ('ID', pa.string()),
    ('Description', pa.string()),
    ('Type', pa.string()),
    ('Number', pa.string())
])
hdrcols = pa.array([i.info() for i in header], type=struct_t).flatten()
names = [fld.name for fld in struct_t]
hdrtbl = pa.Table.from_arrays(hdrcols, names)
# pq.write_table(hdrtbl, f'data/pq/chr{chrom}-header.pq')
