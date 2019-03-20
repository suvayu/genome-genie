from uuid import uuid4

import pytest
import numpy.random as random

from genomegenie.utils import contents


def test_contents(tmp_path):
    jobid = random.randint(10000)
    file_contents = f"{uuid4()}"

    dummy = tmp_path / f"{uuid4()}.o{jobid}"
    dummy.write_text(file_contents)

    assert file_contents == contents(jobid, tmp_path)
