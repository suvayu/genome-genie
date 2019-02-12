from setuptools import setup, find_packages

setup(
    name="genome-genie",
    version="0.dev0",
    description="Genomics toolkit for Python",
    author="Suvayu Ali",
    license="GPLv3",
    python_requires="~=3.6",
    install_requires=[
        "dask",
        "distributed",
        "dask-jobqueue",
        "mako",
        "glom>=19",
        "pandas>=0.24",
        "pyarrow>=0.12",
        "pysam",
    ],
    packages=find_packages(exclude=["tests", "testing"]),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    # entry_points={"console_scripts": ["vcf2pq = genomegenie.cli:vcf2pq"]},
    package_data={"genomegenie.batch": ["templates/*"]},
    data_files=[("share/doc/genome-genie", ["README.md", "docs/pipeline.md"])],
)
