import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('a')
@wfpy.followed_by('b', cond=lambda ctx: False)
@wfpy.followed_by('c')
@wfpy.followed_by('d')
def start(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('aa')
def a(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('ab')
def aa(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('ab')
def b(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('cd')
def c(ctx):
    return True

@wfpy.task()
@wfpy.followed_by('cd')
def d(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('end')
@wfpy.join_point()
def ab(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('end')
@wfpy.join_point()
def cd(ctx):
    return True


@wfpy.task()
@wfpy.join_point()
@wfpy.end_point()
def end(ctx):
    return True
