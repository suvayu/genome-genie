# conding=utf-8
"""Various schemas used to convert VCF to Arrow

@author: Suvayu Ali
@date:   2018-11-06

"""

from collections import OrderedDict

import pyarrow as pa


hdr_t = pa.struct(
    [
        ("HeaderType", pa.string()),
        ("ID", pa.string()),
        ("assembly", pa.string()),
        ("length", pa.string()),
        ("Type", pa.string()),
        ("Number", pa.string()),
        ("Description", pa.string()),
    ]
)

pa_t_map = {
    "Integer": pa.int32(),
    "Float": pa.float32(),
    "String": pa.string(),
    "Flag": pa.bool_(),
    "GT": pa.list_(pa.int8()),  # special case, as pysam converts from string
    # array of UnionArrays are not supported
    # "GT": pa.list_(
    #     pa.union(
    #         [pa.field("phased", pa.bool_()), pa.field("allele_idx", pa.int8())], "dense"
    #     )
    # ),
}

_vcf_cols = OrderedDict(
    CHROM=pa.string(),
    POS=pa.int32(),
    ID=pa.string(),
    REF=pa.string(),
    ALTS=pa.list_(pa.string()),
    QUAL=pa.int8(),
    FILTER=pa.list_(pa.string()),
    FORMAT=pa.list_(pa.string()),
)

_simple_vcf_cols = ["CHROM", "POS", "ID", "REF", "ALTS", "QUAL"]


def get_vcf_cols(hdr, samples):
    df = hdr.query('HeaderType == "INFO"')
    lonely = ["0", "1"]
    # equivalent: df[df.Number.isin(["0", "1"])]
    df1 = df.query(f"Number in {lonely}")  # single value
    df2 = df.query(f"Number not in {lonely}")  # list of values

    # map Type to pyarrow.DataType
    _vcf_cols.update([(f"INFO_{r.ID}", pa_t_map[r.Type]) for i, r in df1.iterrows()])
    _vcf_cols.update(
        [(f"INFO_{r.ID}", pa.list_(pa_t_map[r.Type])) for i, r in df2.iterrows()]
    )

    df = hdr.query('HeaderType == "FORMAT"')
    df1 = df.query(f"Number in {lonely}")  # single value
    df2 = df.query(f"Number not in {lonely}")  # list of values
    _vcf_cols.update(
        [
            (f"{r.ID}_{sample}", pa_t_map[r.Type])
            for i, r in df1.iterrows()
            for sample in samples
        ]
    )
    _vcf_cols.update(
        [
            (f"{r.ID}_{sample}", pa.list_(pa_t_map[r.Type]))
            for i, r in df2.iterrows()
            for sample in samples
        ]
    )
    # HACK: override for Genotype ("GT"), because `pysam` converts the string
    # into values of approriate types: phased (boolean), and values (int)
    if df1.ID.isin(["GT"]).all():
        _vcf_cols.update([(f"GT_{sample}", pa_t_map["GT"]) for sample in samples])

    return _vcf_cols


def get_header(vf, drop_cols=["Description"]):
    """Get header from VariantFile

    vf        -- VariantFile
    drop_cols -- Columns to drop from the final table

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
    if drop_cols:
        return (hdrtbl.to_pandas().drop(columns=drop_cols), samples)
    else:
        return (hdrtbl.to_pandas(), samples)
