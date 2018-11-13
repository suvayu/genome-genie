# conding=utf-8
"""I/O wrappers and utilities

- convert VCF files to Apache Arrow compatible formats
- other I/O utilities

@author: Suvayu Ali
@date:   2018-11-06

"""

from collections import OrderedDict

import pyarrow as pa

from pysam import VariantFile

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


def to_arrow(vfname, batchparams, cols):
    """Convert `VariantRecord` batches to Arrow `RecordBatch`es

    vfname      -- Variant file name to be opened with `VariantFile`
    batchparams -- Parameters to get VariantRecord batch iterator
    cols        -- Record column spec (as returned by get_vcf_cols(..))

    returns list of `RecordBatch`es

    """
    props1 = OrderedDict(
        (c, "alts" if c == "ALT" else c.lower())
        for c in cols
        if not c.startswith("INFO")
    )
    batch = []
    vf = VariantFile(vfname, mode="r", threads=4)
    for vrec in vf.fetch(*batchparams):
        row = OrderedDict((k, getattr(vrec, v)) for k, v in props1.items())
        # vrec.filter: [('NAME', <pysam.libcbcf.VariantHeader>)]
        row["FILTER"] = [i[0] for i in row["FILTER"].items()]
        row.update((f"INFO_{k}", v) for k, v in vrec.info.items())
        batch.append(row)
    vf.close()
    # populate as struct -> flatten
    batch = pa.array(batch, type=pa.struct(cols)).flatten()
    return pa.RecordBatch.from_arrays(batch, pa.schema(cols))

to_arrow1 = to_arrow


def to_parquet(pqwriter, batches):
    """Persist list of `RecordBatch`es to a parquet file

    pqwriter -- parquet output file writer
    batches  -- list of `RecordBatch`es to persist

    """
    tbl = pa.Table.from_batches(batches)
    pqwriter.write_table(tbl, row_group_size=15000)
