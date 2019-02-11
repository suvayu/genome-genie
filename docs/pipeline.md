# Writing data processing pipelines using Genome Genie

Genome genie provides a simple framework to write data processing
pipelines.  The basic premise is, all you need to know are the command
lines to run the different jobs to include a toolchain into your
pipeline.

## What Genome Genie is not

It doesn't retain the state of a job, allow you to rerun, or
reschedule jobs, or manage them as they are running.

## Specifying the pipeline

You can parallelise any set of semantically independent jobs (jobs
without dependencies).  On top of that, the framework parallelises
execution by different input files.  The semantic job dependencies are
specified with a nested list of jobs.  Lists are executed in
seqeuence, whereas tuples are executed in parallel.  The pipeline
elements are essentially names of templates that are used to create
the job script.  Let us look at an example:

    dummyopts = {
        "pipeline": [(["prep1", "ajob"], "bjob"), "finalize"],
        "module": ["package1", "package2"],
        "inputs": [
            {"normal_bam": "normal1.bam", "tumor_bam": "tumor1.bam"},
            {"normal_bam": "normal2.bam", "tumor_bam": "tumor2.bam"},
            {"normal_bam": "normal3.bam", "tumor_bam": "tumor3.bam"},
        ],
        "prep1": {
		    "ref_fasta": "reference.fasta",
			"db": "somedb.vcf",
			"pon": "pon.vcf"
		},
        "ajob": {
            "ref_fasta": "reference.fasta",
            "output": "result1.vcf.gz",
            "db": "somedb.vcf",
            "pon": "pon.vcf",
            "nprocs": 4,
        },
        "bjob": {
            "ref_fasta": "reference.fasta",
            "output": "result2.vcf.gz",
            "db": "somedb.vcf",
            "nprocs": 4,
        },
        "finalize": {
            "inputs": [{"ajob": "result1.vcf.gz", "bjob": "result2.vcf.gz"}],
            "output": "consolidated.parquet",
        },
        "sge": {
            "queue": "short.q",
            "log_directory": "batch",
            "walltime": "00:30:00",
            "cputime": "00:30:00",
            "memory": "16 GB",
        },
    }

In the above specification, the pipeline is specified by the
"pipeline" key.  In this particular case, it is:

    [(["prep1", "ajob"], "bjob"), "finalize"]

Here, as `["prep1", "ajob"]` and `"bjob"` are specified as a `tuple`,
the are executed in parallel, however `"prep1"` and `"ajob"` execute
in sequence (one after the other), as they are inside a `list`.
Similarly, the `"finalize"` job starts after the last of the jobs
inside the tuple are completed.

For a given job, multiple instances are submitted running on the
different input files (three in this case, e.g.: `{"normal_bam":
"normal1.bam", "tumor_bam": "tumor1.bam"}`).  The general job resource
constraints are specified by the sub-dictionary `"sge"`.  Different
resource manager backends (`PBS`, `LSF`, etc) could be integrated by
writing the a template and passing the corresponding options in a
similar dictionary.

For each job type in the pipeline, the job options are also provided
as a sub-dictionary (as seen here).  Certain job types may require to
run over all input files at once, or you might not need any input
files at all.  Such a need is met by "overriding" the `"inputs"` key
in the corresponding sub-dictionary.  This is indicated by:

- `all`: use all input files as input simultaneously
- `ignore`: ignore the inputs
- an arbitrary dictionary allows you to completely override the input
  files by providing an alternate set of files.

The default input files for all jobs in the pipeline are provided as a
list of dictionaries, where the dictionary keys represent the input
file in the job template.  The list is specified under the `"inputs"`
key.

Required modules for all the jobs are specified as list under the key
`"modules"`.  Please note, the specification does not allow you to
provide isolated environments between the different jobs.  So if you
need to run jobs in incompatible environments, you would need to run
separate pipelines.

## Writing templates

As our template language, we use
[`Mako`](https://docs.makotemplates.org/en/latest/syntax.html).
