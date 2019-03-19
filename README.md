

# A toolset for data pipelines in Genomics
[![Build Status](https://travis-ci.com/suvayu/genome-genie.svg?branch=master)](https://travis-ci.com/suvayu/genome-genie)

## Dependencies

- `numpy`
- `pandas`
- `dask`
- `dask.distributed`
- `jinja2`
- `glom`
- `pyarrow`
- `pysam`

# Instructions

- Clone the source code with git:

        $ git clone https://github.com/suvayu/genome-genie.git

- Install dependencies: all dependencies are available on conda-forge
  or PyPI, except for `glom`.  Which is available only on PyPI.  If
  you are using `conda`, you may install like this:

        $ conda install --file requirements-conda.txt
		$ pip3 install [--user] glom

  If you are using `pip`, you may install like this:

        $ pip3 install [--user] -r requirements.txt

- To update (if you have not made any local changes), simply run:

        $ git pull

- Install Genome Genie

        $ cd genome-genie
		$ pip3 install [--user] . -e
		
  The `-e` will allow you to update Genome Genie easily (no need to
  install again).
