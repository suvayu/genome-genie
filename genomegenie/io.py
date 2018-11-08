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
