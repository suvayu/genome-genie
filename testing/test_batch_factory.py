import pytest
from pathlib import Path
from textwrap import dedent

from genomegenie.batch.factory import (template_vars_impl, compile_template, template_dir)


_test_tmpl_dir_ = str(Path(__file__).parent / "templates")


def test_template_vars():
    tmpl1 = """A list of vars: ${var1}, ${var2}"""
    tmpl2 = """${'undefined' if var is UNDEFINED else 'defined'}"""
    tmpl_w_pyblk = dedent("""
    % if var is UNDEFINED:
    something
    % endif
    """)

    assert all(v in template_vars_impl(tmpl1) for v in ('var1', 'var2'))
    assert 'var' in template_vars_impl(tmpl2)
    assert 'var' in template_vars_impl(tmpl_w_pyblk)


sge_opts = {
    "name": "test-job",
    "queue": "short.q",
    "log_directory": "batch",
    "walltime": "00:30:00",
    "cputime": "00:30:00",
    "memory": "16 GB",
    "nprocs": 2,
}


@pytest.mark.parametrize("tmpl, tmpl_dir, opts", [
    # test changing template directory
    ("sge", template_dir(), sge_opts),
    ("sge", _test_tmpl_dir_, sge_opts),
    # test errors: wrong template, wrong template directory, bad options
    pytest.param("sge", "nonexistent", sge_opts, marks=pytest.mark.xfail),
    pytest.param("nonexistent", _test_tmpl_dir_, sge_opts, marks=pytest.mark.xfail),
    pytest.param("sge", _test_tmpl_dir_, dict(), marks=pytest.mark.xfail),
])
def test_compile_template(tmpl, tmpl_dir, opts):
    assert compile_template(tmpl, tmpl_dir, **opts)
