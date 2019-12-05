Examples
========


Simple
------

Whole worfklow is build from tasks and connections between them.

Tasks are functions with ``task()`` decorator and connection between tasks is
defined by ``followed_by()`` decorator. First argument of ``followed_by()``
decorator is name of next tasks, that should be executed when current task is
finished.

Tasks names are intentionally strings so you don't need to care about imports or
order of declarations in file. But that is not requirement, ``followed_by()``
also accept other tasks (function decorated with ``task()``).

.. literalinclude:: examples/simple.py

Workflow can be converted to graph. Nice to have in documentation or for
debugging purposes. Even this workflow is pretty simple, real-world workflow can
be complex with lot of tasks declared across many files, with conditional
branches, ...

.. graphviz:: examples/simple.gv

Finally, workflow can be executed. Example script that will execute workflow from
example above.

.. literalinclude:: examples/simple_run.py

Output from script ::

    INFO:wfepy.workflow:Executing task start
    INFO:wfepy.workflow:Task start is complete
    INFO:wfepy.workflow:Executing task make_coffee
    INFO:wfepy.workflow:Task make_coffee is complete
    INFO:wfepy.workflow:Executing task drink_coffee
    INFO:wfepy.workflow:Task drink_coffee is waiting

    INFO:root:Workflow is not finished, trying run it again...
    INFO:wfepy.workflow:Executing task drink_coffee
    INFO:wfepy.workflow:Task drink_coffee is waiting

    INFO:root:Workflow is not finished, trying run it again...
    INFO:wfepy.workflow:Executing task drink_coffee
    INFO:wfepy.workflow:Task drink_coffee is complete
    INFO:wfepy.workflow:Executing task end
    INFO:wfepy.workflow:Task end is complete
    INFO:wfepy.workflow:Reached end point end

Task ``drink_coffee`` was waiting for something and no other tasks could be
executed, so process stopped.

Waiting tasks are tasks that returned ``False`` while finished tasks must return
``True``. This allow implement waiting for events, for example when user must
add comment to Jira task before process can continue.


Branches
--------

Task can be also followed by multiple tasks so process will be executing
multiple task branches in parallel. Task are not executed in parallel by threads
or processes but it still can be used to execute as much as possible tasks if
task in one branch is waiting.

Looking at coffee drinking example, you can do some other things while waiting
until coffee and while drinking.

.. literalinclude:: examples/branches.py

Task ``start`` has multiple ``followed_by`` decorations so when this task
finish, process will expand followed by list and start executing tasks from both
branches. In the end of workflow branches are joined in ``end`` task. Join
points must be explicitly marked by ``join_point`` decorator to avoid mistakes.

If you forgot to mark join point (or start point or end point)
:meth:`wfepy.Workflow.check_graph` will raise error and you should fix it.

.. graphviz:: examples/branches.gv
