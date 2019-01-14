# coding=utf-8
"""Job templates for SGE jobs in Genomics

@author: Suvayu Ali
@date:   2019-01-09

"""

import os
from copy import deepcopy
from importlib import import_module

from mako.lookup import TemplateLookup
from mako import lexer, codegen

from genomegenie.utils import raise_if_not, consume


def template_dir():
    curdir = os.path.dirname(os.path.realpath(__file__))
    return f"{curdir}/templates"


def command(template, **options):
    """Generate command string from Mako template and options"""
    lookup = TemplateLookup(directories=[template_dir()], default_filters=[])
    template = lookup.get_template(template)
    return template.render(**options)


def template_opts(template):
    with open("/".join([template_dir(), template]), "r") as template:
        # see: https://stackoverflow.com/a/23577289
        mylexer = lexer.Lexer(template.read())
        node = mylexer.parse()
        compiler = lambda: None  # dummy compiler
        compiler.reserved_names = set()
        options = codegen._Identifiers(compiler, node).undeclared

        filters = import_module(".filters", "genomegenie.batch")
        consume(
            map(options.discard, [k for k in dir(filters) if not k.startswith("__")])
        )
        return options


__TOOLS__ = ["gatk", "muse", "strelka", "freebayes"]


def validate(opts):
    """Raises ValueError if options are invalid/incomplete"""

    raise_if_not([opts["tool"]], __TOOLS__, "Unsupported toolset")

    _opts = dict((tool, template_opts(tool)) for tool in __TOOLS__)
    mandatory_somatic = deepcopy(_opts["gatk"])
    consume(
        map(
            mandatory_somatic.intersection_update,
            [_opts[t] for t in ["gatk", "muse", "strelka"]],
        )
    )
    mandatory_germline = deepcopy(_opts["gatk"])
    consume(
        map(
            mandatory_somatic.intersection_update,
            [_opts[t] for t in ["gatk", "freebayes", "strelka"]],
        )
    )

    if "somatic" == opts["run_type"]:
        raise_if_not(mandatory_somatic, opts, "Missing mandatory option")
    elif "germline" == opts["run_type"]:
        raise_if_not(mandatory_germline, opts, "Missing mandatory option")
    else:
        pass
    return
