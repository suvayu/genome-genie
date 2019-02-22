# coding=utf-8
"""Job templates for SGE jobs in Genomics

@author: Suvayu Ali
@date:   2019-01-09

"""

import logging
from pathlib import Path
from importlib import import_module

from jinja2 import (
    meta,
    FileSystemLoader,
    Environment,
    TemplateError,
    UndefinedError,
    make_logging_undefined,
    Undefined,
)

from genomegenie.utils import consume

logger = logging.getLogger(__name__)


def template_dir():
    return str(Path(__file__).parent / "templates")


def compile_template(template, tmpl_dirs, debug=False, **options):
    """Generate command string from Jinja2 template and options"""
    loader = FileSystemLoader(searchpath=tmpl_dirs)

    if debug == False:
        undefined_t = Undefined
    elif debug == True or not issubclass(debug, Undefined):
        # LoggingUndefined w/ it's own logger
        _logger = logging.getLogger(f"genomegenie.batch.templates.{template}")
        undefined_t = make_logging_undefined(logger=_logger)
        if debug != True:
            # warn when debug was unknown custom undefined
            logger.warning(f"Ignoring {debug}, not a subclass of Undefined")
    else:
        # custom undefined, e.g. DebugUndefined
        undefined_t = debug

    env = Environment(
        loader=loader, trim_blocks=True, lstrip_blocks=True, undefined=undefined_t
    )

    # add custom filters to env
    filters = import_module(".filters", "genomegenie.batch")
    env.filters.update(
        (k, getattr(filters, k)) for k in dir(filters) if not k.startswith("_")
    )

    try:
        template = env.get_template(template)
        return template.render(options)
    except TemplateError:
        logger.error(f"Failed to render '{template}' from '{tmpl_dirs}'", exc_info=True)

    return ""


def template_vars(template):
    """Find the variables in a template"""
    with open("/".join([template_dir(), template]), "r") as template:
        return template_vars_impl(template.read())


def template_vars_impl(template_str):
    # see: https://stackoverflow.com/a/8284419/289784
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    tmpl_ast = env.parse(template_str)
    options = meta.find_undeclared_variables(tmpl_ast)

    filters = import_module(".filters", "genomegenie.batch")
    consume(map(options.discard, [k for k in dir(filters) if not k.startswith("_")]))
    return options
