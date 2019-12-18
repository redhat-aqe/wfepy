WfEpy
=====

**WfEpy (Workflow Engine for Python)** is Python library for creating workflows
and automating processes. It is designed to be as simple as possible so
developers can focus on tasks logic, not how to execute workflow, store state,
etc.

Basic features
------------

The library provides the following features:

* Workflow defined in code, via decorators
* Flat workflow structure
* Visualisation features (via graphviz)
* Partial execution model (workflow can be triggered multiple times until
  final completion)
* Allows long running tasks (can be weeks/months or more) without persistent
  processes
* No scheduler included, but can be triggered by cron
* Serialization / deserialization included
* Multiple start and end points are supported


The library adds some restrictions:

* Workflow functions must return boolean, where:

  * `True` means the task has completed and workflow can be advanced
  * `False` means the task is still waiting (e.g. for user input)

* Workflow functions carry around a `context` object (normally a dict)


Details
------------

The workflow is defined via decorators attached to functions, such as:

.. code:: python

    @wfepy.task()
    @wfepy.start_point()
    @wfepy.followed_by('make_coffee')
    def start(context):
        ...

    @wfepy.task()
    @wfepy.followed_by('drink_coffee')
    def make_coffee(context):
        ...

    @wfepy.task()
    @wfepy.followed_by('end')
    def drink_coffee(context):
        ...

    @wfepy.task()
    @wfepy.end_point()
    def end(context):
        ...


A function can be followed by multiple functions:

.. code:: python

    @wfepy.task()
    @wfepy.followed_by('add_sugar')
    @wfepy.followed_by('add_milk')
    def make_coffee(context):
        ...


A function can be conditionally followed by another function:

.. code:: python

    @wfepy.task()
    # only make foam when we've been requested 'cappucino'
    @wfepy.followed_by('make_foam', lambda context: context.data.get('cappucino'))
    # always add milk
    @wfepy.followed_by('add_milk')
    def make_coffee(context):
        ...


Execution model
------------

WfEpy does not provide any scheduler, but can be triggered by cron. It works on
a partial-execution model, meaning it can be triggered multiple times.

The workflow is attempted on every execution, but will only end when at least
one of the end points have been reached. If the workflow can't be ended during an
execution, then the state (including user data and currently-waiting tasks) is
exported/serialized for the next attempt.


.. code:: python

    import coffee_workflow

    wf = wfepy.Workflow()
    wf.load_tasks(coffee_workflow)

    runner = wf.create_runner()
    if restore_state:
        runner.load('state-file')

    runner.run()

    runner.dump('state-file')


This simple design provides many options on workflow execution and customization.
Most workflow libraries out there require external dependencies like databases,
message bus/queue systems etc. Our library requires no such things, just python
and its package dependencies.


Installation
------------

Install it using pip ::

    pip3 install wfepy

or clone repository ::

    git clone https://github.com/redhat-aqe/wfepy.git
    cd wfepy

and install Python package including dependencies ::

    python3 setup.py install
