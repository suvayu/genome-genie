#!/bin/env python3

import os.path
import time
from concurrent.futures import ProcessPoolExecutor
import asyncio
import gc

import pyarrow as pa
import pyarrow.parquet as pq

from pysam import VariantFile

from genomegenie.schemas import get_vcf_cols, get_header
from genomegenie.io import to_arrow, to_parquet

# data files: {20..22},X,Y
data_t = (
    "data/1KGP/ALL.chr{}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
)
data_x = (
    "data/1KGP/ALL.chrX.phase3_shapeit2_mvncall_integrated_v1b.20130502.genotypes.vcf.gz"
)
data_y = "data/1KGP/ALL.chrY.phase3_integrated_v1b.20130502.genotypes.vcf.gz"

chrom = 20
vfname = data_t.format(chrom)
vf = VariantFile(vfname, mode="r", threads=4)
hdr, samples = get_header(vf)
vf.close()
# hdr.to_parquet("data/1KGP/pq/chr20-header.parquet")

cols = get_vcf_cols(hdr, samples)
schema = pa.schema(cols)
struct = pa.struct(cols)

# run in an asyncio event loop, have better control.
# wait for batches of 4, append to parquet file
loop = asyncio.get_event_loop()
batchsize = 4  # ncores/2
tproc, tio = 0, 0  # timing
pqwriter = pq.ParquetWriter("test.parquet", schema, flavor="spark")
for i in range(0, 64, batchsize):
    with ProcessPoolExecutor(4) as executor:
        t0 = time.process_time()
        tasks = [
            loop.run_in_executor(
                executor,
                to_arrow,
                vfname,
                ("20", j * 1_000_000, (j + 1) * 1_000_000),
                cols,
            )
            for j in range(i, i + batchsize)
        ]
        res = asyncio.gather(*tasks)  # future that gathers all results
        loop.run_until_complete(res)  # ensure future/wait
        t1 = time.process_time()
        res = res.result()  # get results
        res = [i for i in res if i.num_rows > 0]
        if len(res):  # append to file
            to_parquet(pqwriter, res)
        t2 = time.process_time()
        del res  # clean-up memory
        gc.collect()
    tproc += t1 - t0
    tio += t2 - t1
loop.close()
pqwriter.close()

print(f"VCF => Parquet: {tproc:.3f}s CPU, {tio:.3f}s I/O")
