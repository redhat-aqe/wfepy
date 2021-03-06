import unittest

import wfepy


@wfepy.task()
@wfepy.start_point()
@wfepy.followed_by('task_a')
@wfepy.followed_by('task_b', cond=lambda ctx: ctx.fork is True)
def start(ctx):
    ctx.done.add('start')
    return True


@wfepy.task()
@wfepy.followed_by('end')
def task_a(ctx):
    ctx.done.add('task_a')
    return True


@wfepy.task()
@wfepy.followed_by('task_bb')
def task_b(ctx):
    ctx.done.add('task_b')
    return True


@wfepy.task()
@wfepy.followed_by('end')
def task_bb(ctx):
    ctx.done.add('task_bb')
    return True


@wfepy.task()
@wfepy.join_point()
@wfepy.end_point()
def end(ctx):
    ctx.done.add('end')
    return True


class Context:
    def __init__(self, fork):
        self.done = set()
        self.fork = fork


class RunnerConditionsTestCase(unittest.TestCase):
    """
    All tasks in workflow should be executed in single run if condition is
    `True`. Otherwise branch with `task_b` and `task_bb` must be skipped and
    join point `end` must not be blocked by task that was not executed.
    """

    def setUp(self):
        self.workflow = wfepy.Workflow()
        self.workflow.load_tasks(__name__)
        self.workflow.check_graph()

    def test_create(self):
        """Test if runner was created with start points."""
        runner = self.workflow.create_runner()
        self.assertIsInstance(runner, wfepy.Runner)
        self.assertListEqual(runner.state, [('start', wfepy.TaskState.NEW)])

    def test_run_fork(self):
        """Test if run was finished and all tasks executed."""
        context = Context(True)
        runner = self.workflow.create_runner(context)
        runner.run()
        self.assertTrue(runner.finished)
        self.assertSetEqual(context.done,
                            {'start', 'task_a', 'task_b', 'task_bb', 'end'})

    def test_run_not_fork(self):
        """Test if run was finished and tasks that matched condition were executed."""
        context = Context(False)
        runner = self.workflow.create_runner(context)
        runner.run()
        self.assertTrue(runner.finished)
        self.assertSetEqual(context.done, {'start', 'task_a', 'end'})
