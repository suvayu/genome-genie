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
}

_vcf_cols = OrderedDict(
    CHROM=pa.string(),
    POS=pa.int32(),
    ID=pa.string(),
    REF=pa.string(),
    ALT=pa.list_(pa.string()),
    QUAL=pa.int8(),
    FILTER=pa.list_(pa.string()),
    # INFO=pa.NULL,
    # FORMAT=pa.NULL,
)


def get_vcf_cols(hdr):
    df = hdr.query('HeaderType == "INFO"')
    lonely = ["0", "1"]
    # equivalent: df[df.Number.isin(["0", "1"])]
    df1 = df.query(f'Number in {lonely}')  # single value
    df2 = df.query(f'Number not in {lonely}')  # list of values

    # map Type to pyarrow.DataType
    _vcf_cols.update([(f"INFO_{r.ID}", pa_t_map[r.Type]) for i, r in df1.iterrows()])
    _vcf_cols.update(
        [(f"INFO_{r.ID}", pa.list_(pa_t_map[r.Type])) for i, r in df2.iterrows()]
    )

    # TODO: convert FORMAT and sample columns
    return _vcf_cols
