import random
import wfpy


@wfpy.task()
@wfpy.start_point()
@wfpy.followed_by('make_coffee')
@wfpy.followed_by('check_reddit')
def start(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('drink_coffee')
def make_coffee(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('write_some_code')
def check_reddit(ctx):
    return True


@wfpy.task()
@wfpy.followed_by('end')
def write_some_code(ctx):
    return random.choice([True, False])


@wfpy.task()
@wfpy.followed_by('end')
def drink_coffee(ctx):
    return random.choice([True, False])


@wfpy.task()
@wfpy.join_point()
@wfpy.end_point()
def end(ctx):
    return True
