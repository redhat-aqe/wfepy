import random
import wfepy as wf


@wf.task()
@wf.start_point()
@wf.followed_by('make_coffee')
@wf.followed_by('check_reddit')
def start(ctx):
    return True


@wf.task()
@wf.followed_by('drink_coffee')
def make_coffee(ctx):
    return True


@wf.task()
@wf.followed_by('write_some_code')
def check_reddit(ctx):
    return True


@wf.task()
@wf.followed_by('end')
def write_some_code(ctx):
    return random.choice([True, False])


@wf.task()
@wf.followed_by('end')
def drink_coffee(ctx):
    return random.choice([True, False])


@wf.task()
@wf.join_point()
@wf.end_point()
def end(ctx):
    return True
