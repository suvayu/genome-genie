# Writing data processing pipelines

Genome Genie provides a simple framework to write data processing
pipelines.  To specify a pipeline, we only need to know the job
commands and dependencies (sequence of execution).

## What Genome Genie is not

It doesn't retain the state of a job, allow us to rerun, or reschedule
jobs, or manage them as they are running.  However it does provide
debugging hooks, and logs for diagnosis.


# Pipeline

**Task dependencies** can be specified in a simple `list` like syntax.
The dependency applies only on the task start time.  The *dependency
graph may be arbitrarily complex*.  As the pipeline is staged for
execution, independent tasks are *scheduled for execution in
parallel*.

```
[
    (
        ["pon_sample", "pon_consolidate", "gatk"],  # GATK
        "muse"                                      # MuSE
    ),
    "variants"     # compare and consolidate variant calls
]
```

In the above example, the GATK tasks are executed in sequence as they
are inside a Python `list` (square brackets), whereas, the sequence of
GATK and MuSE tasks are executed in parallel if sufficient resources
are available.  This is denoted by wrapping them in a Python `tuple`
(parantheses).  Since the "variants" job is outside the above
mentioned tuple, it waits for the GATK and MuSE pipelines to conclude.

Each task is further *parallelised if there are multiple input files*
and it is possible to split the task into multiple jobs.  This
capability maybe *overriden* with a few different kinds of behaviour:

-   instead of processing the input files individually, process them as
    a sequence of files,
-   ignore the input files entirely, or
-   process an entirely different set of input files, specified on a per
    task-type basis; e.g. for all variant calling using GATK, or for all
    panel-of-normals creation, etc.

This is discussed in detail below.


## Specifying tasks

Every task is defined with a *Jinja2 template*.
[Jinja2](http://jinja.pocoo.org/docs/2.10/templates/) is one of two
major template frameworks available in the Python ecosystem.  It
combines text substitution with the flexibility of customisation with
the help of Python functions.  This allows us to write in a language
where we have *access to faculties of both shell scripting and
Python*.

Each template has a list of variables associated with it.  These can
be specified in the pipeline definition as a Python `dictionary`.  A
typical set of options is shown below:

```
{
    "inputs": [
        {
            "normal_bam": "/path/to/normal1.bam",
            "tumor_bam": "/path/to/tumor1.bam"
        },
        {
            "normal_bam": "/path/to/normal2.bam",
            "tumor_bam": "/path/to/tumor2.bam"
        },
    ],
    "gatk": {  # conf for a somatic variant call by GATK
        "ref_fasta": "/path/to/reference.fa",
        "output": "/path/to/outputdir",
        "db": "/path/to/genomedb.vcf.gz",
        "pon": "/path/to/outputdir/pon.vcf.gz",
        "exome_bed": "/path/to/exome.bed",  # optional
        "nprocs": 4,  # optional
    }
}
```


## Configuring a pipeline

As explained above, a pipeline task dependency graph is specified by a
nested Python `list` or `tuple`.  The elements of this graph are
essentially names of the templates that will be used to create the job
script.  Since we would need to substitute the variables in the
templates with actual values, these options also need to be specified
along with the dependency graph.  The options are Python dictionaries.
So that all the respective tool chains are available to our job
scripts, we also need to specify a list of packages that are to be
enabled with `module`.  The last ingredient that we need are the
resource manager instructions (i.e. `qsub` options).  Again, this is
included as a dictionary in the final configuration.

```
options = {
    "pipeline": [
        (["pon_sample", "pon_consolidate", "gatk"], "muse"),
        "variants",
    ],
    "module": ["gatk-4.0.4.0", "MuSE-1.0"],
    "inputs": [
        {
            "normal_bam": "/path/to/normal1.bam",
            "tumor_bam": "/path/to/tumor1.bam",
        },
        {
            "normal_bam": "/path/to/normal2.bam",
            "tumor_bam": "/path/to/tumor2.bam",
        },
    ],
    "pon_sample": {
        "ref_fasta": "/path/to/reference.fa",
        "output": "/path/to/outputdir",
        "db": "/path/to/genomedb.vcf.gz",
        "exome_bed": "/path/to/exome.bed",  # optional
        "nprocs": 4,
    },
    "pon_consolidate": {
        "normals_list": "/path/to/outputdir/normals.txt",
        "output": "/path/to/outputdir",
        "db": "/path/to/genomedb.vcf.gz",
        "pon": "/path/to/outputdir/pon.vcf.gz",
        "nprocs": 4,
    },
    "gatk": {
        "ref_fasta": "/path/to/reference.fa",
        "output": "/path/to/outputdir",
        "db": "/path/to/genomedb.vcf.gz",
        "pon": "/path/to/outputdir/pon.vcf.gz",
        "exome_bed": "/path/to/exome.bed",  # optional
        "nprocs": 4,  # optional
    },
    "muse": {
        "ref_fasta": "/path/to/reference.fa",
        "output": "/path/to/outputdir",
        "db": "/path/to/dbsnp.vcf.gz",
        "exome_bed": "/path/to/exome.bed",  # optional
    },
    "variants": {
        "inputs": [
            {
                "gatk": "/path/to/outputdir/gatk-calls.vcf.gz",
                "muse": "/path/to/outputdir/muse-calls.vcf.gz",
            }
        ]
    },
    "sge": {
        "queue": "dev.q",
        "log_directory": "pipeline",
        "walltime": "24:00:00",
        "cputime": "06:00:00",
        "memory": "64 GB",
    },
}
```

In the above specification, the pipeline is specified by the
`pipeline` key.  The task dependencies have been explained before.
The general resource constraints for each job are specified by the
dictionary under the key `sge`.  In the above example, we ask `sge` to
allocate for jobs each requiring 64 GB of RAM, and 6 hours of CPU
time.  We also allow for a actual runtime of 1 day.  We also need to
specify the queue to submit to, and the log directory.  Note, the log
directory is *relative* to the user's home, and **needs to exist**
before the pipeline is submitted.

For each task type in the pipeline, the options are provided as a
dictionary under a key of the same name.  Certain job types may
require to run over all input files at once, or you might not need any
input files at all, or you might want a different set of input files
all together.  Such a need is met by overriding the `inputs` key in
the corresponding dictionary.  This is indicated by the values:

- `all`: use all input files as input simultaneously (e.g. the
  `pon_consolidate` task)
- `ignore`: ignore the inputs
- an arbitrary dictionary allows you to completely override the input
  files by providing an alternate set of files (as in the `variants`
  task).

The default input files for all jobs in the pipeline are provided as a
list of dictionaries, where the dictionary keys represent the input
file variable in the job template.  The list is specified under the
`inputs` key.

Required modules for all the jobs are specified as a list under the
key `modules`.  Please note, the specification does not allow you to
provide isolated environments between the different jobs.  So *if you
need to run jobs in incompatible environments, you would need to run
separate pipelines*.

Detailed instructions on how to write `Jinja2` templates can be found
in (templates.md).

### Note for developers/advanced users

Almost all parent dictionary keys in the pipeline configuration
represent a template behind the scenes; so almost everything is
configurable by simply writing a template, and including the
configuration variables under the appropriate key in the final
pipeline options.  E.g. switching from `SGE` to a different resource
manager backend like `PBS` is as simple as copying the `sge` template
to `pbs`, and replacing `#$` with `#PBS`!

If, for example, you want to manage your tool chain with something
other than `module`, say `conda`, it will require a little more
effort.  Apart from writing a template for `conda` and including its
configuration, we will also need to adjust the source a bit:
specifically, replace `module` with `conda` in `Pipeline.process(..)`
and `BatchJob`.
