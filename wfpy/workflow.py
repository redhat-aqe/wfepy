import sys
import functools
import itertools
import enum
import pickle
import logging

import attr


logger = logging.getLogger(__name__)


class WorkflowError(RuntimeError):
    pass


@attr.s
class Workflow:
    tasks = attr.ib(factory=dict, init=False)

    def load_tasks(self, module):
        if isinstance(module, str):
            logger.debug('Getting module %s by name from sys.modules', module)
            module = sys.modules[module]
        # load all tasks from module
        duplicates = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, Task):
                if name in self.tasks and self.tasks[name] != obj:
                    logger.error('Duplicate task %s from %s', name, module.__file__)
                    duplicates.append(name)
                else:
                    logger.debug('Loaded task %s from %s', name, module.__file__)
                    self.tasks[name] = obj
        if duplicates:
            raise WorkflowError('Duplicate tasks: ' + ",".join(name))
        # rebuild graph
        for name, task in self.tasks.items():
            for transition in task.followed_by:
                if transition.dest not in self.tasks:
                    continue
                if transition not in self.tasks[transition.dest].preceeded_by:
                    self.tasks[transition.dest].preceeded_by.add(name)

    @property
    def start_points(self):
        return [name for name, task in self.tasks.items() if task.is_start_point]

    @property
    def end_points(self):
        return [name for name, task in self.tasks.items() if task.is_end_point]

    def check_graph(self, strict=True):
        problems = []
        for name, task in self.tasks.items():
            for transition in task.followed_by:
                if transition.dest not in self.tasks:
                    problems.append('Missing task %s.' % transition.dest)
            if not task.followed_by and not task.is_end_point:
                problems.append('Task %s has no ongoing transitions '
                                'but is not marked as end point.' % name)
            if not task.preceeded_by and not task.is_start_point:
                problems.append('Task %s has no incoming transitions '
                                'but is not marked as start point.' % name)
            if len(task.preceeded_by) > 1 and not task.is_join_point:
                problems.append('Task %s has multiple incoming transitions '
                                'but is not marked as join point.' % name)
            if len(task.preceeded_by) == 1 and task.is_join_point:
                problems.append('Task %s has single incoming transition '
                                'and is marked as join point.' % name)
        if problems:
            for msg in problems:
                logger.error(msg)
            raise WorkflowError('Invalid graph! ' + ' '.join(problems))

    def create_runner(self, *args, **kwargs):
        return Runner(self, *args, **kwargs)


@attr.s
class Runner:
    workflow = attr.ib()
    context = attr.ib(default=None)
    state = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        self.state = [(task, TaskState.NEW) for task in self.workflow.start_points]

    def load(self, file_path):
        with open(file_path, 'rb') as f:
            for key, value in pickle.load(f).items():
                setattr(self, key, value)

    def dump(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump({
                'state': self.state,
                'context': self.context,
            }, f)

    @property
    def finished(self):
        return not self.state

    def run(self):
        self.state = self._prepare(self.state)
        while any(task_state not in {TaskState.WAITING, TaskState.BLOCKED}
                  for _, task_state in self.state):
            self.state = self._step(self.state)

    def _prepare(self, state):
        next_state = []
        for task_name, task_state in state:
            if task_state == TaskState.WAITING:
                logger.debug('Task %s is ready now, was waiting', task_name)
                task_state = TaskState.READY
            next_state.append((task_name, task_state))
        return next_state

    def _step(self, state):
        next_state = []
        for task_name, task_state in state:
            task = self.workflow.tasks[task_name]

            if task_state == TaskState.NEW:
                if task.is_join_point:
                    # Join points must be merged, can't process them in this loop.
                    next_state.append((task_name, TaskState.BLOCKED))
                else:
                    logger.debug('Task %s is ready now, was new', task_name)
                    next_state.append((task_name, TaskState.READY))

            elif task_state == TaskState.READY:
                logger.info('Executing task %s', task_name)
                result = task(self.context)
                if not isinstance(result, bool):
                    logger.warning(
                        'Task %s returned %r but should have return True or False '
                        'wheter task has been completed or not. Result will be '
                        'converted to bool implicitly or to True if result is None.',
                        task_name, result
                    )
                    if result is None:
                        result = True
                if result:
                    logger.info('Task %s is complete', task_name)
                    next_state.append((task_name, TaskState.COMPLETE))
                else:
                    logger.info('Task %s is waiting', task_name)
                    next_state.append((task_name, TaskState.WAITING))

            elif task_state == TaskState.COMPLETE:
                if task.is_end_point:
                    logger.info('Reached end point %s', task_name)
                else:
                    logger.debug('Expanding task %s', task_name)
                for transition in task.followed_by:
                    new_state = TaskState.NEW
                    if transition.cond and not transition.cond(self.context):
                        new_state = TaskState.CANCELLED
                    logger.debug('Enqueue new task %s, from %s',
                                 transition.dest, task_name)
                    next_state.append((transition.dest, new_state))

            elif task_state == TaskState.CANCELLED:
                if task.is_join_point:
                    next_state.append((task_name, TaskState.CANCELLED))
                else:
                    logger.info('Task %s execution was canceled by condition',
                                task_name)
                    for transition in task.followed_by:
                        logger.debug('Enqueue new task %s, from %s',
                                     transition.dest, task_name)
                        next_state.append((transition.dest, TaskState.CANCELLED))

            else:
                next_state.append((task_name, task_state))

        return self._joining_step(next_state)

    def _joining_step(self, state):
        next_state = []
        join_points = []

        for task_name, task_state in state:
            task = self.workflow.tasks[task_name]
            if task.is_join_point and task_state in {TaskState.BLOCKED,
                                                     TaskState.CANCELLED}:
                join_points.append((task_name, task_state))
            else:
                next_state.append((task_name, task_state))

        grouped = itertools.groupby(sorted(join_points, key=lambda i: i[0]),
                                    key=lambda i: i[0])
        for join_name, join_list in grouped:
            join_list = list(join_list)
            join_task = self.workflow.tasks[join_name]

            if len(join_task.preceeded_by) == len(join_list):
                logger.debug('Joining tasks %s to task %s',
                             ', '.join(join_task.preceeded_by), join_name)
                if all(s == TaskState.CANCELLED for _, s in join_list):
                    next_state.append((join_name, TaskState.CANCELLED))
                else:
                    next_state.append((join_name, TaskState.READY))

            else:
                blocked_by = set(join_task.preceeded_by) - set(n for n, _ in join_list)
                logger.debug('Join task %s cannot be unblocked, waiting for %s '
                             'to finish', join_name, ', '.join(blocked_by))
                for _, join_state in join_list:
                    next_state.append((join_name, join_state))

        return next_state


@enum.unique
class TaskState(enum.Enum):
    NEW = 1         # task is new in queue
    WAITING = 2     # task is waiting for condition
    BLOCKED = 6     # task is waiting for completion of preceeding tasks
    READY = 3       # task is ready for execution
    COMPLETE = 4    # task was executed and will be expanded
    CANCELLED = 5   # task was not executed because of condition was not met


@attr.s(hash=True)
class Transition:
    dest = attr.ib()
    cond = attr.ib(default=None)

    def __attrs_post_init__(self):
        if isinstance(self.dest, Task):
            self.dest = self.dest.name
        if not isinstance(self.dest, str):
            raise TypeError('Invalid type of destination %s, must be instance '
                            'of Task or string.' % type(self.dest))


@attr.s(hash=True)
class Task:
    func = attr.ib()
    name = attr.ib()

    followed_by = attr.ib(factory=set, init=False)
    preceeded_by = attr.ib(factory=set, init=False)

    is_start_point = attr.ib(default=False, init=False)
    is_join_point = attr.ib(default=False, init=False)
    is_end_point = attr.ib(default=False, init=False)

    def __attrs_post_init__(self):
        functools.update_wrapper(self, self.func)

    @name.default
    def name_default(self):
        return self.func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


@attr.s
class DecoratorStack:
    """
    Utility to collect function decorators and execute them in reverse order at
    once.
    """

    function = attr.ib()
    decorator_list = attr.ib(factory=list)

    def add_decorator(self, decorator):
        """Add decorator to stack. """
        if not callable(decorator):
            raise ValueError('Decoration must be callable')
        self.decorator_list.append(decorator)

    def apply_to(self, func):
        """
        Apply decorators to func and return new func created by chain of
        decorators.

        Return value of each function is used as argument of next function and
        first function will receive ``func`` as argument.
        """
        for decorator in reversed(self.decorator_list):
            func = decorator(func)
        return func

    @classmethod
    def create(cls, func):
        """Create new :class:`DecoratorStack` from function or other stack."""
        if isinstance(func, cls):
            return func
        return cls(func)

    @classmethod
    def add(cls, decorator):
        """
        Create decorator function that will create :class:`DecoratorStack` using
        :meth:`create` and add decorator to list of decorators.
        """
        def inner(func):
            stack = cls.create(func)
            stack.add_decorator(decorator)
            return stack
        return inner

    @classmethod
    def reduce(cls, decorator):
        """
        Create decorator function that will create :class:`DecoratorStack` using
        :meth:`create`, add decorator to list of decorators and aplly decorators
        from stack to decorated function.
        """
        def inner(func):
            stack = cls.create(func)
            obj = decorator(stack.function)
            stack.apply_to(obj)
            return obj
        return inner


def task(*args, **kwargs):
    """
    Decorator to mark function as workflow task. See :class:`Task` for arguments
    docomentation.
    """
    def decorator(func):
        return Task(func, *args, **kwargs)
    return DecoratorStack.reduce(decorator)


def followed_by(*args, **kwargs):
    """
    Add transition to next task. See :class:`Transition` for argumets
    documentation.
    """
    def decorator(func):
        func.followed_by.add(Transition(*args, **kwargs))
        return func
    return DecoratorStack.add(decorator)


def start_point():
    """Mark task as start point. See :class:`Task`."""
    def decorator(func):
        func.is_start_point = True
        return func
    return DecoratorStack.add(decorator)


def join_point():
    """Mark task as join point. See :class:`Task`."""
    def decorator(func):
        func.is_join_point = True
        return func
    return DecoratorStack.add(decorator)


def end_point():
    """Mark task as end point. See :class:`Task`."""
    def decorator(func):
        func.is_end_point = True
        return func
    return DecoratorStack.add(decorator)
