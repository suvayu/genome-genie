# coding=utf-8
"""Job templates for SGE jobs in Genomics

@author: Suvayu Ali
@date:   2019-01-09

"""

from pathlib import Path
from importlib import import_module

from mako.lookup import TemplateLookup
from mako import lexer, codegen
from mako.exceptions import text_error_template

from genomegenie.utils import consume


def template_dir():
    return str(Path(__file__).parent / "templates")


def compile_template(template, tmpl_dir, **options):
    """Generate command string from Mako template and options"""
    # dir_t = template_dir() if dir_t is None else dir_t
    lookup = TemplateLookup(directories=[tmpl_dir], default_filters=[])
    try:
        template = lookup.get_template(template)
        return template.render(**options)
    except:
        print(f"Failed to render '{template}' from '{tmpl_dir}':")
        print(text_error_template().render())
        return ""


def template_vars(template):
    """Find the variables in a template"""
    with open("/".join([template_dir(), template]), "r") as template:
        return template_vars_impl(template.read())


def template_vars_impl(template_str):
    # see: https://stackoverflow.com/a/23577289
    mylexer = lexer.Lexer(template_str)
    node = mylexer.parse()
    compiler = lambda: None  # dummy compiler
    compiler.reserved_names = set()
    options = codegen._Identifiers(compiler, node).undeclared

    filters = import_module(".filters", "genomegenie.batch")
    consume(
        map(options.discard, [k for k in dir(filters) if not k.startswith("_")])
    )
    return options
