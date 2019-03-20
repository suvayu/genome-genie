#!/usr/bin/env python3
# coding=utf-8
"""Pipeline script"""

import logging
from argparse import ArgumentParser

from dask.distributed import Client, LocalCluster

from genomegenie.batch.jobs import Pipeline
from genomegenie.batch.factory import template_dir
from genomegenie.utils import results, contents, job_status, read_config
from genomegenie.cli import RawArgDefaultFormatter, logger_config


parser = ArgumentParser(description=__doc__, formatter_class=RawArgDefaultFormatter)
parser.add_argument("options", help="JSON option file")
loglvls = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
parser.add_argument("--log-level", default="INFO", choices=loglvls)
parser.add_argument("-l", "--log-file")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument(
    "-t", "--template-dir", default=template_dir(), help="Template directory"
)


if __name__ == "__main__":
    opts = parser.parse_args()

    jobopts = read_config(opts.options)
    # prepend input dir to sample filenames
    for infiles in jobopts["inputs"]:
        for key, value in infiles.items():
            infiles[key] = f"{jobopts['inputdir']}/{value}"

    debug = opts.debug
    loglevel = "DEBUG" if debug else opts.log_level

    try:
        logfile = opts.log_file
    except AttributeError:
        logfile = None

    logger = logging.getLogger("genomegenie")
    fmt = "{levelname}:{asctime}:{name}:{lineno}: {message}"
    logger = logger_config(logger, fmt, loglevel, logfile)

    cluster = LocalCluster(n_workers=4, processes=True, memory_limit="1GB")
    client = Client(cluster)

    pipeline = Pipeline(jobopts)
    pipeline.debug = debug
    pipeline.tmpl_dir = opts.template_dir

    staged = pipeline.stage(
        pipeline.graph, pipeline.process, pipeline.submit, monitor_t=1800
    )
    res = staged.compute()
    df = results(res, cols=["script"] if debug else ["jobid", "out", "err", "script"])

    if not debug:  # get logs, find job status
        logs = df.jobid.apply(get_contents, args=(jobopts["sge"]["log_directory"],))
        status = logs.apply(job_status)
        df = df.assign(log=logs, success=status)
        summary = df["success", "jobid"].groupby("success").count()
        logger.info("Pipeline summary:\n" + summary.to_string())

    df.to_parquet("pipeline-scripts.parquet")
    logger.info("Wrote scripts and logs to 'pipeline-scripts.parquet'")
    logger.debug("Summary:\n" + df.to_string())

    # shutdown cluster
    client.close()
    cluster.close()
