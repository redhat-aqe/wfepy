import logging

import attr
import wfepy as wf


@wf.task()
@wf.start_point()
@wf.followed_by('middle')
def start(ctx):
    return True


@wf.task()
@wf.followed_by('end')
def middle(ctx):
    return True


@wf.task()
@wf.end_point()
def end(ctx):
    return True


@attr.s
class Runner(wf.Runner):
    executed_tasks = attr.ib(factory=set, init=False)

    def load(self, json_data):
        data = json.loads(json_data)
        self.context = data['context']
        # In JSON dump is stored name of TaskState, not value (see dump method).
        self.state = [(name, getattr(wf.TaskState, istate))
                      for name, istate in data['state']]

    def dump(self):
        return json.dumps({
            'context': self.context,
            # We want nice human readable state in JSON output.
            'state': [(name, istate.name) for name, istate in self.state],
        })

    def task_execute(self, task):
        # Custom task execute code. We can add custom pre/post hooks, logging,
        # pass extra variables to tasks (by defalt only context is passed to
        # tasks) ... we can even prevent some task from executing and fake their
        # results.

        self.executed_tasks.add(task.name)

        retval = task(self.context)  # or `super().execute(task)`

        if not retval and task.has_labels({'user'}):
            logging.info('Waiting for user input in task %s.', task.name)

        return retval


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    workflow = wf.Workflow()
    workflow.load_tasks(__name__)

    # Use custom runner instead of default one.
    runner = Runner(workflow)
    runner.run()

    assert runner.executed_tasks == {'start', 'middle', 'end'}
