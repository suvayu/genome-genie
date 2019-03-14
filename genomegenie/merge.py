# conding=utf-8
"""Utilities to merge various variant calls

@author: Suvayu Ali
@date:   2019-01-13

"""

import logging

import numpy as np
import pandas as pd
import dask.dataframe as dd


logger = logging.getLogger(__name__)


def collate(samecaller=False, source="allel"):
    if source not in ("allel", "pysam"):
        logger.error(f"Unknown provenance: {source}, supported sources: allel, pysam")
        return
    ...
