import unittest

import wfepy


@wfepy.task()
@wfepy.start_point()
@wfepy.followed_by('blocked')
@wfepy.followed_by('not_blocked')
def start(ctx):
    ctx.done.add('start')
    return True


@wfepy.task()
@wfepy.followed_by('end')
def blocked(ctx):
    ctx.done.add('blocked')
    return not ctx.blocked


@wfepy.task()
@wfepy.followed_by('end')
def not_blocked(ctx):
    ctx.done.add('not_blocked')
    return True


@wfepy.task()
@wfepy.join_point()
@wfepy.end_point()
def end(ctx):
    ctx.done.add('end')
    return True


class Context:
    def __init__(self):
        self.done = set()
        self.blocked = True


class RunnerWaitingBranchesTestCase(unittest.TestCase):
    """
    Task `blocked` is waiting until `ctx.blocked` is changed to `False`.

    Similar to test case in `test_waiting`, task `blocked` should be executed
    again and again. But this test case is testing waiting on join points.
    Branch with task `not_blocked` should be executed but before executing `end`
    task all preceeding tasks must be finished, including `blocked` task.
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

    def test_run(self):
        """Test if run was finished and all tasks executed."""
        context = Context()
        runner = self.workflow.create_runner(context)

        runner.run()
        self.assertFalse(runner.finished)
        self.assertSetEqual(context.done, {'start', 'blocked', 'not_blocked'})

        runner.run()
        self.assertFalse(runner.finished)
        self.assertSetEqual(context.done, {'start', 'blocked', 'not_blocked'})

        context.blocked = False

        runner.run()
        self.assertTrue(runner.finished)
        self.assertSetEqual(context.done, {'start', 'blocked', 'not_blocked', 'end'})
