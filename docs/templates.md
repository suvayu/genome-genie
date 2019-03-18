# Writing Jinja2 templates for your tasks

Jinja2 provides common control structures like `if..else..`, and
`for`-loops.  We can also write Python functions to do more complex
tasks in a jinja template.  A overview of the relevant capabilities
are below.

Anything inside double curly braces (`{{ ... }}`) are considered for
substitution.  Whereas control structures are wrapped in `{% ... %}`.
When a variable referenced in a template hasn't been defined, it is
set to `undefined`.  Which can then be handled appropriately in
Python.  By default, a failed substitution like this is removed from
the template.  So on rendering a template like this:

    This is a {{ foo }}, and that is a {{ bar }}.

where `bar` is `"tree"`, but `foo` is undefined, the final rendered
text looks like:

    This is a , and that is a tree.

Genome Genie provides interfaces (and helper scripts) to debug
situations like this easier.  These are discussed in a latter section.

## Using conditions and control structures

The flow of how a template is rendered can be controlled by
`if..else..` statements like this:

```
{% if foo is undefined %}
do this
{% else %}
do something with {{ undefined }}
{% endif %}
```

We can also use control structures like `for`-loops.

```
{% for fname in filenames %}
do something with {{ fname }}
{% endfor %}
```

## Using Python functions to do complex tasks

To perform more complex tasks, we can use custom Python filters
functions.  A filter function takes one mandatory positional argument,
with any number of optional arguments.

```
{{ list_of_names | join(", ") }}
```

The above snippet converts a list of names into a comma-separated
string of names.  If we need custom filters, we can write them to
match the signature: `myfilter(value, opt1=val1, opt2=val2, ...)`, and
put them in [filters.py](../genomegenie/batch/filters.py**, and they
will be automatically available in all our templates.  You may see
that file for some examples.

**Note for advanced users**: In an earlier section it was mentioned
when variables in a templates are not defined, they are replaced with
`undefined`.  These objects are actually instances of an `Undefined`
class.  When writing your own filter functions, you may also handle
these errors - there are examples in `filters.py`.

## Debugging your template

Genome Genie has various ways of handling `undefined` the helper
script [`debug-templates.py`](../bin/debug-templates.py) is provided
to easily use these different debugging modes.

- `debug` (default): in case a variable is undefined, the variable is
  left as is.  E.g., the how the `sge` template is rendered as shown
  below when the `name` and `nprocs` variables are undefined.
  
        $ bin/debug-templates.py etc/sge-opts.json -t sge
        INFO:2019-03-18 17:15:54,421:genomegenie:48: Rendering 'sge' from '/path/to/genomegenie/batch/templates' ...
        INFO:2019-03-18 17:15:54,449:genomegenie:52:
        #
        #$ -N {{ name }}
        #$ -q short.q
        #$ -j y
        #$ -o batch/
        #$ -l h_rt=00:30:00
        #$ -l h_cpu=00:30:00,h_vmem=16 GB
        #$ -pe smp {{ nprocs }}
        #

- `log`: the missing variables are sent to the log as a warning

        $ bin/debug-templates.py etc/sge-opts.json -t sge -m log
        INFO:2019-03-18 17:44:19,137:genomegenie:48: Rendering 'sge' from '/path/to/genomegenie/batch/templates' ...
        WARNING:2019-03-18 17:44:19,142:genomegenie.batch.templates.sge:718: Template variable warning: name is undefined
        WARNING:2019-03-18 17:44:19,142:genomegenie.batch.templates.sge:718: Template variable warning: nprocs is undefined
        INFO:2019-03-18 17:44:19,142:genomegenie:52:
        #
        #$ -N
        #$ -q short.q
        #$ -j y
        #$ -o batch/
        #$ -l h_rt=00:30:00
        #$ -l h_cpu=00:30:00,h_vmem=16 GB
        #$ -pe smp
        #

- `strict`: this mode crashes the script when it encounters an
  undefined variable, making it impossible for you to miss any errors.
  Note, this crashes at the first error, so when in this mode, you can
  only spot one undefined variable at a time.
  
        $ bin/debug-templates.py etc/sge-opts.json -t sge -m strict
        INFO:2019-03-18 17:48:48,049:genomegenie:48: Rendering 'sge' from '/home/sali/genome-genie/genomegenie/batch/templates' ...
        ERROR:2019-03-18 17:48:48,074:genomegenie.batch.factory:63: Failed to render '<Template 'sge'>' from '/home/sali/genome-genie/genomegenie/batch/templates'
        Traceback (most recent call last):
          File "/home/sali/genome-genie/genomegenie/batch/factory.py", line 61, in compile_template
            return template.render(options)
          File "/home/sali/miniconda3/lib/python3.6/site-packages/jinja2/asyncsupport.py", line 76, in render
            return original_render(self, *args, **kwargs)
          File "/home/sali/miniconda3/lib/python3.6/site-packages/jinja2/environment.py", line 1008, in render
            return self.environment.handle_exception(exc_info, True)
          File "/home/sali/miniconda3/lib/python3.6/site-packages/jinja2/environment.py", line 780, in handle_exception
            reraise(exc_type, exc_value, tb)
          File "/home/sali/miniconda3/lib/python3.6/site-packages/jinja2/_compat.py", line 37, in reraise
            raise value.with_traceback(tb)
          File "/home/sali/genome-genie/genomegenie/batch/templates/sge", line 8, in top-level template code
            #$ -pe smp {{ nprocs }}
        jinja2.exceptions.UndefinedError: 'name' is undefined
        INFO:2019-03-18 17:48:48,090:genomegenie:52:

## Reference and examples

You may look at the existing
[templates](../genomegenie/batch/templates/) to better understand
through examples how to write a template from scratch.  For detailed
documentation on the Jinja2 template language see the [official
documentation](http://jinja.pocoo.org/docs/2.10/templates/).
