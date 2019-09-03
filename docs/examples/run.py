import sys
import os
import logging

import click

import wfpy
import wfpy.utils


@click.command()
@click.option('-d', '--debug', is_flag=True)
@click.argument('example_name')
def run_wf(debug, example_name):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    example_module = __import__(example_name)

    wf = wfpy.Workflow()
    wf.load_tasks(example_module)

    wfpy.utils.render_graph(wf, os.path.join(os.path.dirname(__file__), example_name + '.gv'))

    runner = wf.create_runner()
    runner.run()


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    run_wf()

