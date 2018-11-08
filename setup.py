from setuptools import setup, find_packages

setup(
    name="genome-genie",
    version="0.dev0",
    description="Genomics toolkit for Python",
    author="Suvayu Ali",
    license="GPLv3",
    # include_package_data=True,
    packages=find_packages(exclude=["tests", "testing"]),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    entry_points={"console_scripts": ["vcf2pq = genomegenie.cli:vcf2pq"]},
    # package_data={"electrumpersonalserver": ["data/*"]},
    data_files=[("share/doc/genome-genie", ["README.md"])],
)
