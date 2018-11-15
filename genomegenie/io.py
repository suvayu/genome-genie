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


def to_arrow(vfname, batchparams, cols, nested_props=("FILTER", "FORMAT")):
    """Convert `VariantRecord` batches to Arrow `RecordBatch`es

    The returned Arrow buffer breaks compatibility with a standard VCF column
    header: ALT -> ALTS.  This is because `pysam.VariantRecord` does this, and
    it makes sense.  This also significantly reduces code complexity.

    The keys nested under the INFO column are completely free-form, so they are
    detected automatically from the VCF file header.  During conversion to
    Arrow buffer, filling these fields present a significant book-keeping
    challenge (they can also be nested!).  So we opt to fill these
    semi-automatically, and any absent fields are set to NULL (thanks to
    Arrow!).

    Note, while converting to other formats, these may need to be filled by
    reasonable alternatives; which might come at a cost.  For example, Pandas
    does not support NULLs, and a likely replacement would be numpy.na.  This
    means you firstly lose zero-copy conversion, and possibly convert the field
    type to a float!  Beware.

    vfname      -- Variant file name to be opened with `VariantFile`
    batchparams -- Parameters to get VariantRecord batch iterator
    cols        -- Record column spec (as returned by get_vcf_cols(..))

    returns list of `RecordBatch`es

    """
    batch = []
    vf = VariantFile(vfname, mode="r", threads=4)  # FIXME:
    for vrec in vf.fetch(*batchparams):
        # break compatibility with VCF file column header: ALT -> ALTS.
        # INFO_* fields are filtered out as they are handled separately later.
        row = OrderedDict(
            (c, getattr(vrec, c.lower())) for c in cols if not c.startswith("INFO")
        )
        for prop in nested_props:
            # vrec.{prop}: [('NAME', <pysam.libcbcf.VariantMetadata>)]
            row[prop] = [i[0] for i in row[prop].items()]
        # missing INFO_* fields are treated as NULLs (see doc string)
        row.update((f"INFO_{k}", v) for k, v in vrec.info.items())
        batch.append(row)
    vf.close()  # FIXME:
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
