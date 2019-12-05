import wfepy as wf


@wf.task()
@wf.start_point()
@wf.followed_by('make_coffee')
def start(ctx):
    # All tasks must return True or False if they were finished or waiting for
    # some external event or something and must be executed again later.
    return True


@wf.task()
@wf.followed_by('drink_coffee')
def make_coffee(ctx):
    return True


@wf.task()
@wf.followed_by('end')
def drink_coffee(ctx):
    import random
    if not random.choice([True, False]):
        # Still drinking. Returing False means this task was not completed and
        # must be executed again on next run.
        return False
    return True


@wf.task()
@wf.end_point()
def end(ctx):
    return True
