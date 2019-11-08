import wfepy as wf


@wf.task()
@wf.start_point()
@wf.followed_by('task_ab')
def start_a(ctx):
    return True


@wf.task()
@wf.start_point()
@wf.followed_by('task_ab')
def start_b(ctx):
    return True


@wf.task()
@wf.followed_by('task_a')
@wf.followed_by('task_b')
@wf.join_point()
def task_ab(ctx):
    return True


@wf.task()
@wf.followed_by('task_xy')
def task_a(ctx):
    return True


@wf.task()
@wf.followed_by('task_xy')
def task_b(ctx):
    return True


@wf.task()
@wf.followed_by('task_x')
@wf.followed_by('task_y')
@wf.join_point()
def task_xy(ctx):
    return True

@wf.task()
@wf.end_point()
def task_x(ctx):
    return True


@wf.task()
@wf.end_point()
def task_y(ctx):
    return True
