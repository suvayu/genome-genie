# coding=utf-8
"""Job templates for SGE jobs in Genomics

@author: Suvayu Ali
@date:   2019-01-09

"""

import os
from importlib import import_module

from mako.lookup import TemplateLookup
from mako import lexer, codegen
from mako.exceptions import text_error_template

from genomegenie.utils import consume


def template_dir():
    curdir = os.path.dirname(os.path.realpath(__file__))
    return f"{curdir}/templates"


def compile_template(template, **options):
    """Generate command string from Mako template and options"""
    lookup = TemplateLookup(directories=[template_dir()], default_filters=[])
    try:
        template = lookup.get_template(template)
        return template.render(**options)
    except:
        print(text_error_template().render())
        # raise


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
