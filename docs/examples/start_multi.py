import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('task_ab')
def start_a(ctx):
    return True


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('task_ab')
def start_b(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('task_a')
@wfpy.followed_by('task_b')
@wfpy.join_point()
def task_ab(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('task_xy')
def task_a(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('task_xy')
def task_b(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('task_x')
@wfpy.followed_by('task_y')
@wfpy.join_point()
def task_xy(ctx):
    return True

@wfpy.task()
@wfpy.end_point()
def task_x(ctx):
    return True


@wfpy.task()
@wfpy.end_point()
def task_y(ctx):
    return True
