import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('create_bugzilla')
@wfpy.followed_by('create_jira')
def start(ctx):
    print('file bug...')
    return True


@wfpy.task()
@wfpy.followed_by('complete')
def create_bugzilla(ctx):
    print('creating bugzilla...')
    return True


@wfpy.task()
@wfpy.followed_by('complete')
def create_jira(ctx):
    print('creating jira...')
    return True


@wfpy.task()
@wfpy.end_point()
def complete(ctx):
    print('done...')
    return True
