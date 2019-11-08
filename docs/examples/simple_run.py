import logging
import wfepy
import wfepy.utils

logging.basicConfig(level=logging.INFO)


# Import module with tasks.
import simple


# Create new workflow.
wf = wfepy.Workflow()
# Load tasks from module and add them to workflow.
wf.load_tasks(simple)
# Check if graph is OK, all tasks are defined, decorated correctly, ...
wf.check_graph()

# Render graph.
wfepy.utils.render_graph(wf, 'basic.gv')

# Create runner for workflow.
runner = wf.create_runner()

# Execute workflow.
runner.run()

# Check if workflow finished, no tasks are waiting.
while not runner.finished:
    logging.info('Workflow is not finished, trying run it again...')
    runner.run()
