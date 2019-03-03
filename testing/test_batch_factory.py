from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import pytest
from jinja2 import StrictUndefined

from genomegenie.batch.factory import template_vars_impl, compile_template, template_dir


_test_tmpl_dir_ = str(Path(__file__).parent / "templates")


def test_template_vars():
    tmpl1 = """A list of vars: {{ var1 }}, {{ var2 }}"""
    tmpl2 = dedent(
        """
    {% if var is undefined %}
    undefined
    {% else %}
    defined
    {% endif %}
    """
    )

    assert all(v in template_vars_impl(tmpl1) for v in ("var1", "var2"))
    assert "var" in template_vars_impl(tmpl2)


sge_opts = {
    "name": "test-job",
    "queue": "short.q",
    "log_directory": "batch",
    "walltime": "00:30:00",
    "cputime": "00:30:00",
    "memory": "16 GB",
    "nprocs": 2,
}


# test changing template directory
@pytest.mark.parametrize("tmpl_dir", [template_dir(), _test_tmpl_dir_,])
def test_compile_template(tmpl_dir):
    assert compile_template("sge", tmpl_dir, **sge_opts)


def test_compile_template_loggingundefined(caplog):
    opts = deepcopy(sge_opts)
    opts.pop("nprocs")
    assert compile_template("sge", template_dir(), True, **opts)

    for record in caplog.records:
        assert record.levelname == "WARNING"


# In the case of simple replacements, Jinja2 templates silently skips
# undefined variables, so enable strict undefined
def test_compile_template_strictundefined(caplog):
    opts = deepcopy(sge_opts)
    opts.pop("nprocs")
    compile_template("sge", template_dir(), StrictUndefined, **opts)

    assert "UndefinedError" in caplog.text
    for record in caplog.records:
        assert record.levelname == "ERROR"


@pytest.mark.parametrize(
    "tmpl, tmpl_dir",
    [
        # wrong template, wrong template directory, bad options
        pytest.param("sge", "nonexistent"),
        pytest.param("nonexistent", _test_tmpl_dir_),
    ],
)
def test_compile_template_render_err(caplog, tmpl, tmpl_dir):
    compile_template(tmpl, tmpl_dir, **sge_opts)

    assert "Failed to render" in caplog.text
    for record in caplog.records:
        assert record.levelname == "ERROR"
