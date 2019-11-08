import unittest

import wfepy


@wfepy.task()
@wfepy.start_point()
@wfepy.followed_by('fail')
def start(ctx):
    ctx.done.append('start')
    return True


@wfepy.task()
@wfepy.followed_by('end')
def fail(ctx):
    ctx.done.append('fail')
    if ctx.fail:
        raise RuntimeError
    return True


@wfepy.task()
@wfepy.end_point()
def end(ctx):
    ctx.done.append('end')
    return True


class Context:
    def __init__(self):
        self.done = list()
        self.fail = True


class RunnerExceptionTestCase(unittest.TestCase):
    """
    When task raise exception runner must stop with correct state. Task that
    raised exception must remain in READY state and other tasks untouched and
    scheduled for next run. When problem is resolved proccess must continue.
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

        with self.assertRaises(RuntimeError):
            runner.run()
        self.assertFalse(runner.finished)
        self.assertListEqual(context.done, ['start', 'fail'])

        with self.assertRaises(RuntimeError):
            runner.run()
        self.assertFalse(runner.finished)
        self.assertListEqual(context.done, ['start', 'fail', 'fail'])

        context.fail = False

        runner.run()
        self.assertTrue(runner.finished)
        self.assertListEqual(context.done, ['start', 'fail', 'fail', 'fail', 'end'])
