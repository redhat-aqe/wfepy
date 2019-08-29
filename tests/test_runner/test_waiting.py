import unittest

import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('blocked')
def start(ctx):
    ctx.done.append('start')
    return True


@wfpy.task()
@wfpy.followed_by('end')
def blocked(ctx):
    ctx.done.append('blocked')
    return not ctx.blocked


@wfpy.task()
@wfpy.end_point()
def end(ctx):
    ctx.done.append('end')
    return True


class Context:
    def __init__(self):
        self.done = list()
        self.blocked = True


class RunnerWaitingTestCase(unittest.TestCase):
    """
    Task `blocked` is waiting until `ctx.blocked` is changed to `False`.

    When `ctx.blocked == False` only `start` and `blocked` task should be
    executed and `blocked` should be executed again in next run if `ctx.blocked`
    is still `False`.

    After change `ctx.blocked` to `True`, task `blocked` should be executed last
    time and runner should reach final `end` state.
    """

    def setUp(self):
        self.workflow = wfpy.Workflow()
        self.workflow.load_tasks(__name__)
        self.workflow.check_graph()

    def test_create(self):
        """Test if runner was created with start points."""
        runner = self.workflow.create_runner()
        self.assertIsInstance(runner, wfpy.Runner)
        self.assertListEqual(runner.state, [('start', wfpy.TaskState.NEW)])

    def test_run(self):
        """Test if run was finished and all tasks executed."""
        context = Context()
        runner = self.workflow.create_runner(context)

        runner.run()
        self.assertFalse(runner.finished)
        self.assertListEqual(context.done, ['start', 'blocked'])

        runner.run()
        self.assertFalse(runner.finished)
        self.assertListEqual(context.done, ['start', 'blocked', 'blocked'])

        context.blocked = False

        runner.run()
        self.assertTrue(runner.finished)
        self.assertListEqual(context.done,
                             ['start', 'blocked', 'blocked', 'blocked', 'end'])
