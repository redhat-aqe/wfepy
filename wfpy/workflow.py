import sys
import functools
import collections

import attr


@attr.s
class Workflow:
    context = attr.ib(default=None)
    tasks = attr.ib(factory=dict, init=False)
    state = attr.ib(default=None, init=False)

    def load_tasks(self, module):
        # load all tasks from module
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, WorkflowItem):
                if name in self.tasks and self.tasks[name] != obj:
                    raise RuntimeError(f'Duplicate task {name}')
                self.tasks[name] = obj
        # rebuild graph
        for name, task in self.tasks.items():
            for transition in task.followed_by:
                if transition.func not in self.tasks:
                    continue
                if transition not in self.tasks[transition.func].preceeded_by:
                    self.tasks[transition.func].preceeded_by.append(name)

    @property
    def start_points(self):
        return {name: task for name, task in self.tasks.items() if task.is_start_point}

    @property
    def end_points(self):
        return {name: task for name, task in self.tasks.items() if task.is_end_point}

    def check_graph(self):
        for name, task in self.tasks.items():
            missing_tasks = [t.func for t in task.followed_by
                             if t.func not in self.tasks]
            if missing_tasks:
                raise RuntimeError(f'Missing tasks {missing_tasks!r}')
            if not task.followed_by and not task.is_end_point:
                raise RuntimeError(f'Invalid graph! Task {name} has no outgoing '
                                   'transitions and is not marked as end point')
            if not task.preceeded_by and not task.is_start_point:
                raise RuntimeError(f'Invalid graph! Task {name} has no incoming '
                                   'transitions and is not marked as start point')
            if len(task.preceeded_by) > 1 and not task.is_join_point:
                raise RuntimeError(f'Invalid graph! Task {name} has multiple incoming '
                                   'transitions and is not marked as join point')
            if len(task.preceeded_by) == 1 and task.is_join_point:
                raise RuntimeError(f'Invalid graph! Task {name} has single incoming '
                                   'transition and is marked as join point')

    def run(self):
        self.check_graph()

        if self.state is None:
            self.state = [(task, None) for task in self.start_points.values()]

        self.state = [(task, task_flag or None) for task, task_flag in self.state]
        while any(task_flag is not False for _, task_flag in self.state):
            self.state = self.step(self.state)

        return not self.state   # empty state = reached end point

    def step(self, state):
        next_state = []
        for task, task_flag in state:
            # task was already executed in previous step - expand it
            if task_flag is True:
                # TODO check length of new states, if <1 then task must be join
                # point or end point, otherwise it is bug in condition - end
                # from non-end point
                next_state.extend([
                    (self.tasks[transition.func], None)
                    for transition in task.followed_by
                    if not transition.cond or transition.cond(self.context)
                ])
            # task wasn't executed
            elif task_flag is None:
                if task.is_join_point and len(state) > 1:
                    next_state.append((task, None))
                else:
                    task_new_state = task(self.context)
                    if task_new_state is None:
                        task_new_state = True
                    next_state.append((task, task_new_state))
            # task cannot be executed in this step
            else:
                next_state.append((task, False))
        # merge join tasks
        if all(task.is_join_point for task, _ in next_state):
            deduplicated_next_state = []
            for i in next_state:
                if i not in deduplicated_next_state:
                    deduplicated_next_state.append(i)
            if len(deduplicated_next_state) > 1:
                raise RuntimeError('Deadlock! Tasks could not be joined')
            next_state = deduplicated_next_state
        return next_state


@attr.s
class WorkflowItem:
    func = attr.ib()
    title = attr.ib()

    followed_by = attr.ib(factory=list, init=False)
    preceeded_by = attr.ib(factory=list, init=False)

    is_start_point = attr.ib(default=False, init=False)
    is_join_point = attr.ib(default=False, init=False)
    is_end_point = attr.ib(default=False, init=False)

    def __attrs_post_init__(self):
        functools.update_wrapper(self, self.func)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


@attr.s
class WorkflowTransition:
    func = attr.ib()
    cond = attr.ib(default=None)


@attr.s
class WorkflowItemBuilder:
    func = attr.ib()
    decorations = attr.ib(factory=lambda: collections.defaultdict(list))

    def add_decoration(self, name, *args, **kwargs):
        self.decorations[name].append((args, kwargs))

    def build_item(self, *args, **kwargs):
        item = WorkflowItem(self.func, *args, **kwargs)

        item.followed_by = [
            WorkflowTransition(*args, **kwargs)
            for args, kwargs in self.decorations['followed_by']
        ]

        item.is_start_point = bool(self.decorations['start_point'])
        item.is_join_point = bool(self.decorations['join_point'])
        item.is_end_point = bool(self.decorations['end_point'])

        return item

    @classmethod
    def create(cls, func):
        if isinstance(func, cls):
            return func
        return cls(func)


def item(*args, **kwargs):
    def decorator(func):
        return WorkflowItemBuilder.create(func).build_item(*args, **kwargs)
    return decorator


def decorator_factory(name):
    def outer(*args, **kwargs):
        def inner(func):
            builder = WorkflowItemBuilder.create(func)
            builder.add_decoration(name, *args, **kwargs)
            return builder
        return inner
    return outer


sys.modules[__name__].__getattr__ = decorator_factory
