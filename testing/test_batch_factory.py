from textwrap import dedent

import pytest

from genomegenie.batch.factory import template_vars_impl


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
