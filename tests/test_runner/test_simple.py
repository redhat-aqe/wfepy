import unittest

import wfepy


@wfepy.task()
@wfepy.start_point()
@wfepy.followed_by('first')
def start(ctx):
    ctx.add('start')
    return True


@wfepy.task()
@wfepy.followed_by('second')
def first(ctx):
    ctx.add('first')
    return True


@wfepy.task()
@wfepy.followed_by('end')
def second(ctx):
    ctx.add('second')
    return True


@wfepy.task()
@wfepy.end_point()
def end(ctx):
    ctx.add('end')
    return True


class RunnerSimpleTestCase(unittest.TestCase):
    """
    All tasks in workflow should be executed in single run.
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
        context = set()
        runner = self.workflow.create_runner(context)
        runner.run()
        self.assertTrue(runner.finished)
        self.assertSetEqual(context, {'start', 'first', 'second', 'end'})
