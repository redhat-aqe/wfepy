WfEpy
=====

**WfEpy (Workflow Engine for Python)** is Python library for creating workflows
and automating various processes. It is designed to be as simple as possible so
developers can focus on tasks logic, not how to execute workflow, store state,
etc.

Individual steps in workflow are simply functions with decorator and transitions
between tasks are also defined by decorators. Everything what developer needs to
do is add few decorators to functions that implements tasks logic. This library
is then used to build graph from tasks and transitions and execute tasks in
workflow by traversing graph and calling task functions. Context passed to each
function is arbitrary user object that can be used to store data, connect to
other services or APIs, ...

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

WfEpy does not provide any server scheduler or something like that. It was
designed to be used in scripts, that are for example periodically executed by
cron. If workflow have task that cannot be finished in single run library
provides way how to store current state of runner including user data and
restore it on next run.

.. code:: python

    import coffee_workflow

    wf = wfepy.Workflow()
    wf.load_tasks(coffee_workflow)

    runner = wf.create_runner()
    if restore_state:
        runner.load('state-file')

    runner.run()

    runner.dump('state-file')

This simple design provides many options how to execute your workflow and
customize it. This was also reason why this library was created, we don't want
to manage new service/server that executes few simple workflows. We would like
to use service we already have, for example Jenkins, cron, ...


Installation
------------

Install it using pip ::

    pip3 install wfepy

or clone repository ::

    git clone https://github.com/redhat-aqe/wfepy.git
    cd wfepy

and install Python package including dependencies ::

    python3 setup.py install
