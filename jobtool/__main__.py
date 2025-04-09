"""
A jobfolder is a directory that has the structure
|- .
|- ..
|- initial.traj    (Required)
|- log.txt         (optional)
|- results.traj    (optional)
|-     :           (optional)
"""
import os
import sys
import click
import pathlib

import ase
import ase.io
import ase.visualize

from jobtool.walker import Status
from jobtool.api import get_jobfolders


@click.group()
def cli() -> None: ...


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", help='File where results are stored. Default is stdout.')
@click.option("--include", type=click.STRING, multiple=True, help="Statuses that are included in the results list")
@click.option("--exclude", type=click.STRING, multiple=True, help="Statuses that are excluded from the results list",)
@click.option("--format", type=click.STRING, default='json', show_default=True, help='Format of the results. Can be either json or csv.')
@click.option("--with-status/--without-status", type=click.BOOL, default=True, help="If provided, status is removed from output")
@click.option("--lines-checked", type=click.IntRange(min=1, max=100), help="Number of lines check in end of log file to determine status.")
def jobfolders(folder: os.PathLike, output: None | os.PathLike, **options) -> None:
    """Generate a list of all the jobfolders in a given directory tree"""
    options = {name: value for name, value in options.items() if value is not None}  # Remove non-provided options from options dict
    if output:
        with open(output) as filewrapper:
            get_jobfolders(folder, output=filewrapper, **options)
    else:
        get_jobfolders(folder, output=sys.stdout, **options)


@cli.command()
def get_status_list() -> None:
    """Print all valid status values"""
    click.echo("Valid statuses:")
    click.echo("--------------")
    for status in Status:
        click.echo(f"- {status.value}")


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path))
def display_converged(folder: os.PathLike) -> None:
    ase.visualize.view([
        ase.io.read(path.joinpath('results.traj'))
        for path in get_jobfolders(folder, include=Status.CONVERGED, with_status=False, format='none')
    ])


if __name__ == '__main__':
    cli()
