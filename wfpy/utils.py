import graphviz


def render_graph(workflow, output, format='png'):
    dot = graphviz.Digraph('Workflow')

    def task_style(task):
        if task.is_end_point or task.is_start_point:
            return 'bold,filled'
        return 'solid,filled'

    def task_color(task):
        if task.is_end_point:
            return 'red'
        elif task.is_start_point:
            return 'green'
        return 'white'

    def transition_label(trans):
        if trans.cond:
            return 'cond'
        return None

    for name, task in workflow.tasks.items():
        dot.node(name, style=task_style(task), fillcolor=task_color(task))
        for trans in task.followed_by:
            dot.edge(name, trans.dest, label=transition_label(trans))

    dot.render(output, format=format)
