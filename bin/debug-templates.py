#!/usr/bin/env python3
# coding=utf-8
"""Template debugging script"""

import json
import logging
from argparse import ArgumentParser

from jinja2 import DebugUndefined, StrictUndefined

from genomegenie.batch.factory import compile_template, template_dir
from genomegenie.cli import RawArgDefaultFormatter, logger_config


modes = {
    "nodebug": False,
    "debug": DebugUndefined,
    "log": True,
    "strict": StrictUndefined,
}


parser = ArgumentParser(description=__doc__, formatter_class=RawArgDefaultFormatter)
parser.add_argument("options", help="JSON option file")
loglvls = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
parser.add_argument("--log-level", default="INFO", choices=loglvls)
parser.add_argument("-l", "--log-file")
parser.add_argument("-m", "--mode", default="debug", choices=modes.keys())
parser.add_argument("--template-dir", default=template_dir(), help="Template directory")
parser.add_argument("-t", "--template", help="Template to render")


if __name__ == "__main__":
    opts = parser.parse_args()

    with open(opts.options, "r") as jsonfile:
        template_vars = json.load(jsonfile)

    try:
        logfile = opts.log_file
    except AttributeError:
        logfile = None

    logger = logging.getLogger("genomegenie")
    fmt = "{levelname}:{asctime}:{name}:{lineno}: {message}"
    logger = logger_config(logger, fmt, "DEBUG", logfile)

    logger.info(f"Rendering '{opts.template}' from '{opts.template_dir}' ...")
    rendered = compile_template(
        opts.template, opts.template_dir, debug=modes[opts.mode], **template_vars
    )
    logger.info("\n" + rendered)
