from collections import OrderedDict
from time import sleep

import pytest
import numpy as np
import pyarrow as pa
from pysam import VariantFile
from dask.distributed import LocalCluster, Client
from allel import read_vcf

from genomegenie.io import to_arrow, to_df, to_dask_df
from genomegenie.schemas import get_header, get_vcf_cols

from genomegenie.schemas import _simple_vcf_cols


vfname1 = "variant_calls/Sample_1_Strelka.somatic.snvs.vcf"
# vfname2 = "data/1KGP/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
# vfname2 = "data/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"


def test_arrow_pysam():
    vf1 = VariantFile(vfname1, mode="r")
    hdr, samples = get_header(vf1)
    cols = get_vcf_cols(hdr, samples)
    nested_props=("FILTER", "FORMAT")

    batch = to_arrow(vfname1, tuple(), cols)
    tbl = pa.Table.from_batches([batch])
    df = tbl.to_pandas()

    # arr_cols = [isinstance(i, np.ndarray) for i in df.loc[0]]
    # subdf = df[df.columns[arr_cols]]
    # df = df.assign(**subdf.applymap(tuple).to_dict(orient='series'))

    # assert df.all()

    return df


def test_df_allel():
    client = Client()
    # sleep(3)
    df_itr = to_df(vfname1, fields="*", samples=[0, 1])
    df = to_dask_df(df_itr)
    df = df.compute()
    # client.close()
    # assert df.all()

    return df, client
