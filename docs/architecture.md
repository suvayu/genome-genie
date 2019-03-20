# Architecture

Since the toolchain ecosystem in Genomics is so varied, Genome Genie
makes no assumptions about them.  It however assumes the jobs will
execute on a batch cluster, with a shared network file system.

## Requirements

- Genome Genie is compatible with Python 3.6 or higher in the 3.x
  series.  It relies on Dask for managing job dependencies and
  scheduling.

- It assumes the presence of a batch cluster where job scripts are
  submitted with the `qsub` command.  Switching between different
  kinds of batch clusters (SGE, PBS, LSF, etc) is trivial and can be
  done by writing a small template.

- It assumes that the execution environment is setup
  (e.g. enable/disable software packages) using the `module` system.
  Although switching that is relatively trivial, and can be done
  within a few minutes.

- It requires the presence of Samtools to read input file metadata.

## What Genome Genie is not (limitations)

- It doesn't retain the state of a job.  Hence it is not possible to
  rerun, reschedule, or back-fill past jobs.

- It does not provide any mechanism to do live monitoring (besides
  what the batch system might provide), hence a running pipeline
  cannot be paused or resumed, or managed in general.

Despite the above limitations, Genome Genie does provide many
debugging hooks, and an aggregated logging system for diagnosis.

---

### Running jobs in conflicting environments

By default all jobs share the same execution environment, defined by
the top level `module` key.  This however maybe overriden on a
per-task basis.  Say if we wanted to run two different GATK tasks but
with different versions of GATK.  We can then duplicate a template,
and override the loaded modules (as shown below).  Please note, since
the keys correspond to templates, the actual template files need to be
duplicated with the new name.

```
{
    "pipeline": (
        ["pon_sample", "pon_consolidate", "gatk"],
        ["pon_sample2", "pon_consolidate2", "gatk2"],
        "muse"
    ),
    "module": ["samtools-1.9", "gatk-4.0.4.0", "MuSE-1.0"],
    "gatk": {...},
    "gatk2": {
        "module": ["samtools-1.9", "gatk-3"]
        "foo": ...
    }
}
```

### Note for developers

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
