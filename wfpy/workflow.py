import sys
import functools
import itertools
import enum
import pickle
import logging

import attr


logger = logging.getLogger(__name__)


class WorkflowError(RuntimeError):
    """Generic workflow error."""


@attr.s
class Workflow:
    """
    Workflow graph - collection of tasks.

    :ivar task: collection of tasks, dict with tasks name as key
    """

    tasks = attr.ib(factory=dict, init=False)

    def load_tasks(self, module):
        """
        Load tasks from module and add them to workflow graph. Can be also
        module name, then module will be get from `sys.module` by that name.

        :raises WorkflowError: if name of loaded task is not unique
        """
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
            raise WorkflowError('Duplicate tasks: ' + ','.join(name))
        # rebuild graph
        for name, task in self.tasks.items():
            for transition in task.followed_by:
                if transition.dest not in self.tasks:
                    continue
                if transition not in self.tasks[transition.dest].preceded_by:
                    self.tasks[transition.dest].preceded_by.add(name)

    @property
    def start_points(self):
        """List of names of tasks that are marked as start points."""
        return [name for name, task in self.tasks.items() if task.is_start_point]

    @property
    def end_points(self):
        """List of names of tasks that are marked as end points."""
        return [name for name, task in self.tasks.items() if task.is_end_point]

    def check_graph(self, strict=True):
        """
        Check workflow graph - if some task is missing, all task are marked
        properly as start, join or end points, ...

        :raises WorkflowError: when there are some problems with workflow graph
        """
        problems = []
        for name, task in self.tasks.items():
            for transition in task.followed_by:
                if transition.dest not in self.tasks:
                    problems.append('Missing task %s.' % transition.dest)
            if not task.followed_by and not task.is_end_point:
                problems.append('Task %s has no ongoing transitions '
                                'but is not marked as end point.' % name)
            if not task.preceded_by and not task.is_start_point:
                problems.append('Task %s has no incoming transitions '
                                'but is not marked as start point.' % name)
            if len(task.preceded_by) > 1 and not task.is_join_point:
                problems.append('Task %s has multiple incoming transitions '
                                'but is not marked as join point.' % name)
            if len(task.preceded_by) == 1 and task.is_join_point:
                problems.append('Task %s has single incoming transition '
                                'and is marked as join point.' % name)
        if problems:
            for msg in problems:
                logger.error(msg)
            raise WorkflowError('Invalid graph! ' + ' '.join(problems))

    def create_runner(self, *args, **kwargs):
        """Create :class:`Runner` from this workflow."""
        return Runner(self, *args, **kwargs)


@attr.s
class Runner:
    """
    Workflow execution engine.

    :ivar workflow: :class:`Workflow`
    :ivar context: arbitrary user object, passed to all tasks
    :ivar state: state of execution
    """

    workflow = attr.ib()
    context = attr.ib(default=None)
    state = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        self.state = [(task, TaskState.NEW) for task in self.workflow.start_points]

    def load(self, file_path):
        """Load runner from file. See also :meth:`dump`."""
        with open(file_path, 'rb') as f:
            for key, value in pickle.load(f).items():
                setattr(self, key, value)

    def dump(self, file_path):
        """
        Dump runner to file. Stored dump contains :attr:`context` and
        :attr:`state` so runner execution can be restored and finished later.
        """
        with open(file_path, 'wb') as f:
            pickle.dump({
                'state': self.state,
                'context': self.context,
            }, f)

    @property
    def finished(self):
        """
        Workflow execution finished. True when reached end points and there is
        no task that should be executed.
        """
        return not self.state

    def run(self):
        """
        Execute tasks from workflow.

        Some tasks might end in state in which they cannot be executed (waiting
        for external event or join point waiting for preceding tasks). If there
        is no task that can be executed run will stop executing and
        :attr:`finished` property will be ``False``. In that case run should be
        called again (with some delay or runner can be dumped to file by
        :meth:`dump` and executed later).

        See :class:`TaskState` for list of task states.
        """
        self.state = self._prepare(self.state)
        while any(task_state not in {TaskState.WAITING, TaskState.BLOCKED}
                  for _, task_state in self.state):
            self.state, error = self._step(self.state)
            if error is not None:
                raise error

    def _prepare(self, state):
        next_state = []
        for task_name, task_state in state:
            if task_state == TaskState.WAITING:
                logger.debug('Task %s is ready now, was waiting', task_name)
                task_state = TaskState.READY
            next_state.append((task_name, task_state))
        return next_state

    def _step(self, state):
        task_error = None
        next_state = []
        for task_name, task_state in state:
            task = self.workflow.tasks[task_name]

            # Stop processing if there is error.
            if task_error is not None:
                next_state.append((task_name, task_state))
                continue

            if task_state == TaskState.NEW:
                if task.is_join_point:
                    # Join points must be merged, can't process them in this loop.
                    next_state.append((task_name, TaskState.BLOCKED))
                else:
                    logger.debug('Task %s is ready now, was new', task_name)
                    next_state.append((task_name, TaskState.READY))

            elif task_state == TaskState.READY:
                logger.info('Executing task %s', task_name)
                try:
                    result = task(self.context)
                except Exception as e:
                    logger.exception(e)
                    # To not break runner state, exception must be stored and
                    # raised later.
                    task_error = e
                    result = False
                if not isinstance(result, bool):
                    logger.warning(
                        'Task %s returned %r but should have return True or False '
                        'wheter task has been completed or not. Result will be '
                        'converted to bool implicitly or to True if result is None.',
                        task_name, result
                    )
                    if result is None:
                        result = True
                if task_error:
                    logger.error('Task %s failed', task_name)
                    next_state.append((task_name, TaskState.READY))
                elif result:
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
                        new_state = TaskState.CANCELED
                    logger.debug('Enqueue new task %s, from %s',
                                 transition.dest, task_name)
                    next_state.append((transition.dest, new_state))

            elif task_state == TaskState.CANCELED:
                if task.is_join_point:
                    next_state.append((task_name, TaskState.CANCELED))
                else:
                    logger.info('Task %s execution was canceled by condition',
                                task_name)
                    for transition in task.followed_by:
                        logger.debug('Enqueue new task %s, from %s',
                                     transition.dest, task_name)
                        next_state.append((transition.dest, TaskState.CANCELED))

            else:
                next_state.append((task_name, task_state))

        # Can't raise error there, next_state must be stored in run().
        return self._joining_step(next_state), task_error

    def _joining_step(self, state):
        next_state = []
        join_points = []

        for task_name, task_state in state:
            task = self.workflow.tasks[task_name]
            if task.is_join_point and task_state in {TaskState.BLOCKED,
                                                     TaskState.CANCELED}:
                join_points.append((task_name, task_state))
            else:
                next_state.append((task_name, task_state))

        grouped = itertools.groupby(sorted(join_points, key=lambda i: i[0]),
                                    key=lambda i: i[0])
        for join_name, join_list in grouped:
            join_list = list(join_list)
            join_task = self.workflow.tasks[join_name]

            if len(join_task.preceded_by) == len(join_list):
                logger.debug('Joining tasks %s to task %s',
                             ', '.join(join_task.preceded_by), join_name)
                if all(s == TaskState.CANCELLED for _, s in join_list):
                    next_state.append((join_name, TaskState.CANCELLED))
                else:
                    next_state.append((join_name, TaskState.READY))

            else:
                blocked_by = set(join_task.preceded_by) - set(n for n, _ in join_list)
                logger.debug('Join task %s cannot be unblocked, waiting for %s '
                             'to finish', join_name, ', '.join(blocked_by))
                for _, join_state in join_list:
                    next_state.append((join_name, join_state))

        return next_state


@enum.unique
class TaskState(enum.Enum):
    """
    Enumeration of task states.

    :cvar NEW: task new in queue
    :cvar WAITING: task is waiting, function returned ``False``
    :cvar BLOCKED: task is waiting for completion of preceding tasks
    :cvar READY: task is ready for execution
    :cvar COMPLETE: task was executed and will be expanded
    :cvar CANCELED: task was not executed because transition condition was not met

    .. graphviz:: task-state.gv
    """

    NEW = 1
    WAITING = 2
    BLOCKED = 6
    READY = 3
    COMPLETE = 4
    CANCELED = 5


@attr.s(hash=True)
class Transition:
    """
    Transition to following task.

    :ivar dest: name of following task
    :ivar cond: condition whether following task should be executed, function
                that will receive context from :class:`Runner` and must return bool
                (allows to create conditional branching and looping in graph)

    """

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
    """
    Workflow task. Wraps function for use in workflow.

    Wrapped function must accept context from :class:`Runner` via only parameter
    and should return ``True`` or ``False`` whether task was completed and
    execution can continue with following tasks.

    If wrapped function returned ``False`` execution will stop and task will be
    executed again in next run. This way can be implemented waiting, eg. for
    external event.

    :ivar function: wrapped function
    :ivar name: task name (by default function name)
    :ivar followed_by: connection to next tasks (set of :class:`Transition`)
    :ivar preceded_by: names of preceding tasks, generated by :class:`Workflow`
    :ivar is_start_point: task is start point of workflow
    :ivar is_join_point: task is join point of multiple tasks
    :ivar is_end_point: task is end point of workflow
    """

    func = attr.ib()
    name = attr.ib()

    followed_by = attr.ib(factory=set, init=False)
    preceded_by = attr.ib(factory=set, init=False)

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
            raise ValueError('Decorator must be callable')
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
        :meth:`create`, add decorator to list of decorators and apply decorators
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
    documentation.
    """
    def decorator(func):
        return Task(func, *args, **kwargs)
    return DecoratorStack.reduce(decorator)


def followed_by(*args, **kwargs):
    """
    Add transition to next task. See :class:`Transition` for arguments
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
