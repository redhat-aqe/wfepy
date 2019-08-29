import unittest

import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('task_a')
@wfpy.followed_by('task_b')
@wfpy.followed_by('task_c')
@wfpy.followed_by('task_d')
def start(ctx):
    ctx.add('start')
    return True


@wfpy.task()
@wfpy.followed_by('task_x')
def task_a(ctx):
    ctx.add('task_a')
    return True


@wfpy.task()
@wfpy.followed_by('task_ab')
def task_x(ctx):
    ctx.add('task_x')
    return True


@wfpy.task()
@wfpy.followed_by('task_ab')
def task_b(ctx):
    ctx.add('task_b')
    return True


@wfpy.task()
@wfpy.followed_by('task_cd')
def task_c(ctx):
    ctx.add('task_c')
    return True


@wfpy.task()
@wfpy.followed_by('task_cd')
def task_d(ctx):
    ctx.add('task_d')
    return True


@wfpy.task()
@wfpy.followed_by('end')
@wfpy.join_point()
def task_ab(ctx):
    ctx.add('task_ab')
    return True


@wfpy.task()
@wfpy.followed_by('end')
@wfpy.join_point()
def task_cd(ctx):
    ctx.add('task_cd')
    return True


@wfpy.task()
@wfpy.join_point()
@wfpy.end_point()
def end(ctx):
    ctx.add('end')
    return True


class RunnerBranchesTestCase(unittest.TestCase):
    """
    All tasks in workflow should be executed in single run. Some of them may be
    in random order because of branches.
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
        context = set()
        runner = self.workflow.create_runner(context)
        runner.run()
        self.assertTrue(runner.finished)
        self.assertSetEqual(context, {'start', 'task_a', 'task_b', 'task_c', 'task_d',
                                      'task_x', 'task_ab', 'task_cd', 'end'})
