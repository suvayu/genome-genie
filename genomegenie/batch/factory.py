# coding=utf-8
"""Job templates for SGE jobs in Genomics

@author: Suvayu Ali
@date:   2019-01-09

"""

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


def template_dir():
    return str(Path(__file__).parent / "templates")


def compile_template(template, tmpl_dirs, undefined_t=False, **options):
    """Generate command string from Jinja2 template and options"""
    loader = FileSystemLoader(searchpath=tmpl_dirs)

    if undefined_t is True:
        # LoggingUndefined w/ it's own logger
        # _logger = logging.getLogger(__name__)  # FIXME:
        undefined_t = make_logging_undefined()
    elif undefined_t is False:
        undefined_t = Undefined
    else:
        try:
            # custom undefined like DebugUndefined
            assert issubclass(undefined_t, Undefined)
        except AssertionError:
            print(f"Ignoring {undefined_t}, not a subclass of Undefined")
            undefined_t = Undefined

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
        print(f"Failed to render '{template}' from '{tmpl_dirs}'")
    except UndefinedError as err:
        print(f"'{template}': {err}")

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
