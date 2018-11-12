# conding=utf-8
"""I/O wrappers and utilities

- convert VCF files to Apache Arrow compatible formats
- other I/O utilities

@author: Suvayu Ali
@date:   2018-11-06

"""

from collections import OrderedDict, defaultdict
import pdb

import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
import pandas as pd

from genomegenie.schemas import hdr_t, get_vcf_cols


def get_header(vf, drop_cols=["Description"]):
    """Get header from VariantFile

    vf -- VariantFile

    """
    header = [
        dict(Description=rec.value, HeaderType=rec.type)
        if rec.type is "GENERIC"
        else dict(rec, HeaderType=rec.type)
        for rec in vf.header.records
    ]
    header = pa.array(header, type=hdr_t).flatten()
    names = [field.name for field in hdr_t]
    hdrtbl = pa.Table.from_arrays(header, names)
    samples = [i for i in vf.header.samples]
    # TODO: convert FORMAT and sample columns
    if drop_cols:
        return (hdrtbl.to_pandas().drop(columns=drop_cols), samples)
    else:
        return (hdrtbl.to_pandas(), samples)


# NOTE: A couple of alternate implementations of to_arrow(..); the first
# performs marginally better than the other.

## 1: populate as struct -> flatten
def to_arrow(vrec_batch, cols):
    """Convert `VariantRecord` batches to Arrow `RecordBatch`es

    vrec_batch -- VariantRecord batch or VariantRecord batch iterator
    cols       -- Record column spec (as returned by get_vcf_cols(..))

    returns list of `RecordBatch`es

    """
    props1 = OrderedDict(
        (c, "alts" if c == "ALT" else c.lower())
        for c in cols
        if not c.startswith("INFO")
    )
    batch = []
    for vrec in vrec_batch:
        row = OrderedDict((k, getattr(vrec, v)) for k, v in props1.items())
        # vrec.filter: [('NAME', <pysam.libcbcf.VariantHeader>)]
        row["FILTER"] = [i[0] for i in row["FILTER"].items()]
        row.update((f"INFO_{k}", v) for k, v in vrec.info.items())
        batch.append(row)
    # pdb.set_trace()
    batch = pa.array(batch, type=pa.struct(cols)).flatten()
    return pa.RecordBatch.from_arrays(batch, pa.schema(cols))

to_arrow1 = to_arrow


## 2: double loop: iterate over records, and columns
def to_arrow2(vrec_batch, cols):
    """Convert `VariantRecord` batches to Arrow `RecordBatch`es

    vrec_batch -- VariantRecord batch or VariantRecord batch iterator
    cols       -- Record column spec (as returned by get_vcf_cols(..))

    returns list of `RecordBatch`es

    """
    props = ["alts" if c == "ALT" else c for c in cols]
    batch = list([] for _ in range(len(cols)))
    for vrec in vrec_batch:
        for field, col in zip(props, batch):
            if field.startswith("INFO"):
                _, key = field.split("_", 1)
                col.append(vrec.info.get(key, None))
            elif field == "FILTER":
                # vrec.filter: [('NAME', <pysam.libcbcf.VariantHeader>)]
                col.append([i[0] for i in getattr(vrec, field.lower()).items()])
            else:
                col.append(getattr(vrec, field.lower(), None))
    return pa.RecordBatch.from_arrays(
        [pa.array(batch[i], type=cols[c]) for i, c in enumerate(cols)], pa.schema(cols)
    )
