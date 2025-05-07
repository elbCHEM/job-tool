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

import ase
import ase.io
import ase.visualize

from jobtool.jobfolder import get_jobfolders, Status


@click.group()
def cli() -> None: ...


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", help='File where results are stored. Default is stdout.')
@click.option("--include", help="Statuses that are included in the results list", type=click.STRING, multiple=True)
@click.option("--exclude", help="Statuses that are excluded from the results list", type=click.STRING, multiple=True)
@click.option("--format", help='Format of the results. Can be either json or csv.', type=click.STRING, default='json', show_default=True)
@click.option("--without-status", help="If provided, status is removed from output", type=click.BOOL, is_flag=True, default=False)
@click.option('--lines-checked', help="Number of lines check in end of log file to determine status.", type=click.IntRange(min=1, max=100))
def jobfolders(folder: os.PathLike, output: None | os.PathLike, **options) -> None:
    """Generate a list of all the jobfolders in a given directory tree"""
    options = {name: value for name, value in options.items() if value}  # Remove non-provided options from options dict

    if not output:
        return get_jobfolders(folder, output=sys.stdout, **options)
    if isinstance(output, str):
        with open(output, 'w') as filewrapper:
            return get_jobfolders(folder, output=filewrapper, **options)

    raise ValueError(f'Cannot use {output=} as a valid output source')


@cli.command()
def get_status_list() -> None:
    """Print all valid status values"""
    click.echo("Valid statuses:")
    click.echo("--------------")
    for status in Status:
        click.echo(f"- {status.value}")


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
def display_converged(folder: os.PathLike) -> None:
    converged_paths = get_jobfolders(folder, include="CONVERGED", without_status=True)

    resultfiles = [x.joinpath('results.traj') for x in converged_paths]
    trajectories = map(ase.io.read, resultfiles)
    ase.visualize.view(trajectories)


if __name__ == '__main__':
    cli()
