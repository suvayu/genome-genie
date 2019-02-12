# coding=utf-8
"""Validate options

@author: Suvayu Ali
@date:   2019-01-18

"""

from copy import deepcopy

from genomegenie.utils import raise_if_not, consume
from genomegenie.batch.factory import template_vars


__TOOLS__ = ["gatk", "muse", "strelka", "freebayes"]


def validate(opts):
    """Raises ValueError if options are invalid/incomplete"""

    # tool, run_type, opts[tool]

    raise_if_not([opts["tool"]], __TOOLS__, "Unsupported toolchain")

    _opts = dict((tool, template_vars(tool)) for tool in __TOOLS__)
    mandatory_somatic = set(deepcopy(_opts["gatk"]))
    consume(
        map(
            mandatory_somatic.intersection_update,
            [_opts[t] for t in ["gatk", "muse", "strelka"]],
        )
    )
    mandatory_germline = set(deepcopy(_opts["gatk"]))
    consume(
        map(
            mandatory_germline.intersection_update,
            [_opts[t] for t in ["gatk", "freebayes", "strelka"]],
        )
    )

    # print(mandatory_germline)
    # print(mandatory_somatic)

    if "somatic" == opts["run_type"]:
        raise_if_not(mandatory_somatic, opts[opts["tool"]], "Missing mandatory option")
    elif "germline" == opts["run_type"]:
        raise_if_not(mandatory_germline, opts[opts["tool"]], "Missing mandatory option")
    else:
        pass
    return
