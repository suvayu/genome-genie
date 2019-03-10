# conding=utf-8
"""I/O wrappers and utilities

- convert VCF files to Apache Arrow compatible formats
- other I/O utilities

@author: Suvayu Ali
@date:   2018-11-06

"""

from collections import OrderedDict

import pyarrow as pa
import pandas as pd
import dask.dataframe as dd

from pysam import VariantFile
from allel.io.vcf_read import (
    iter_vcf_chunks,
    _prep_fields_param,
    _do_rename,
    _chunk_iter_progress,
    DEFAULT_BUFFER_SIZE,
    DEFAULT_CHUNK_LENGTH,
    DEFAULT_CHUNK_WIDTH,
    DEFAULT_ALT_NUMBER,
    _doc_param_input,
    _doc_param_fields,
    _doc_param_exclude_fields,
    _doc_param_rename_fields,
    _doc_param_types,
    _doc_param_numbers,
    _doc_param_alt_number,
    _doc_param_fills,
    _doc_param_region,
    _doc_param_tabix,
    _doc_param_samples,
    _doc_param_transformers,
    _doc_param_buffer_size,
    _doc_param_chunk_length,
    _doc_param_log,
)

from genomegenie.schemas import _simple_vcf_cols


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
            (c, getattr(vrec, c.lower()))
            for c in cols if c in _simple_vcf_cols
        )
        # vrec.{prop}: [('<filter>', <pysam.libcbcf.VariantMetadata>)]
        row.update(
            (prop, [key for key in getattr(vrec, prop.lower()).keys()])
            for prop in nested_props
        )
        # missing INFO_* fields are treated as NULLs (see doc string)
        row.update((f"INFO_{k}", v) for k, v in vrec.info.items())
        # reverse the layout: fmt in sample -> sample in fmt.  this way
        # for a given FORMAT field, all samples will be in adjacent blocks.
        row.update(
            (f"{fmt}_{sample.name}", (int(sample.phased), *sample.values()[i]))
            for i, fmt in enumerate(row["FORMAT"])
            for sample in vrec.samples.values()
        )
        # NOTE: indexing above slows the generator expr by a factor of two.
        # indexing relies on the fixed ordering of FORMAT field values.
        batch.append(row)
    vf.close()  # FIXME:
    # from pprint import pprint
    # pprint(batch[-1])
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


def to_dask_df(
    input,
    fields=None,
    exclude_fields=None,
    rename_fields=None,
    types=None,
    numbers=None,
    alt_number=DEFAULT_ALT_NUMBER,
    fills=None,
    region=None,
    tabix="tabix",
    samples=None,
    transformers=None,
    buffer_size=DEFAULT_BUFFER_SIZE,
    chunk_length=DEFAULT_CHUNK_LENGTH,
    log=None,
    **kwargs,
):
    """Read data from a VCF file into a dask DataFrame.

    Parameters
    ----------
    input : string or file-like
        {input}

    fields : list of strings, optional
        {fields}

    exclude_fields : list of strings, optional
        {exclude_fields}

    rename_fields : dict[str -> str], optional
        {rename_fields}

    types : dict, optional
        {types}

    numbers : dict, optional
        {numbers}

    alt_number : int, optional
        {alt_number}

    fills : dict, optional
        {fills}

    region : string, optional
        {region}

    tabix : string, optional
        {tabix}

    samples : list of strings
        {samples}

    transformers : list of transformer objects, optional
        {transformers}

    buffer_size : int, optional
        {buffer_size}

    chunk_length : int, optional
        {chunk_length}

    log : file-like, optional
        {log}

    **kwargs : extra keyword arguments
        the extra arguments are passed on to `dask.dataframe.concat`

    Returns
    -------
    df : dask.dataframe.DataFrame

    """

    store_samples, fields = _prep_fields_param(fields)

    # setup
    fields, samples, headers, chunk_itr = iter_vcf_chunks(
        input=input,
        fields=fields,
        exclude_fields=exclude_fields,
        types=types,
        numbers=numbers,
        alt_number=alt_number,
        buffer_size=buffer_size,
        chunk_length=chunk_length,
        fills=fills,
        region=region,
        tabix=tabix,
        samples=samples,
        transformers=transformers,
    )

    if rename_fields:
        rename_fields, chunk_itr = _do_rename(
            chunk_itr, fields=fields, rename_fields=rename_fields, headers=headers
        )

    # setup progress logging
    if log is not None:
        chunk_itr = _chunk_iter_progress(chunk_itr, log, prefix="[to_dask_df]")

    # read chunks and convert to dask dataframe
    ddfs = []
    for _chunk in chunk_itr:
        # VCFChunkIterator returns: chunk, chunk_length, chrom, pos
        chunk = _chunk[0]
        output = dict()

        for key in chunk.keys():
            _key = key.split("/")[1]
            if key.startswith("variants/"):
                output[f"{_key}"] = (
                    [tuple(row) for row in chunk[key]]
                    if len(chunk[key].shape) > 1  # nested
                    else chunk[key]
                )
            elif key.startswith("calldata/"):
                output.update(
                    (
                        f"{sample}_{_key}",
                        [tuple(row) for row in chunk[key][:, i, ...]]
                        if len(chunk[key].shape) > 2  # nested
                        else chunk[key][:, i],
                    )
                    for i, sample in enumerate(samples)
                )
            else:
                print("Whoa!")
        ddfs.append(dd.from_pandas(pd.DataFrame(output), npartitions=1))

    ddf = dd.concat(ddfs, axis=0, interleave_partitions=True, **kwargs)

    return ddf


to_dask_df.__doc__ = to_dask_df.__doc__.format(
    input=_doc_param_input,
    fields=_doc_param_fields,
    exclude_fields=_doc_param_exclude_fields,
    rename_fields=_doc_param_rename_fields,
    types=_doc_param_types,
    numbers=_doc_param_numbers,
    alt_number=_doc_param_alt_number,
    fills=_doc_param_fills,
    region=_doc_param_region,
    tabix=_doc_param_tabix,
    samples=_doc_param_samples,
    transformers=_doc_param_transformers,
    buffer_size=_doc_param_buffer_size,
    chunk_length=_doc_param_chunk_length,
    log=_doc_param_log,
)
