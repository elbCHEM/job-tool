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
import click

import ase
import ase.io
import ase.visualize


from typing import Optional
from jobtool.jobfolder import get_jobfolders, Status


@click.group()
def cli() -> None: ...


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", type=click.STRING, help='File where results are stored. Default is stdout.')
@click.option("--include", type=click.STRING)
@click.option("--exclude", type=click.STRING)
@click.option("--without-status", type=click.BOOL, is_flag=True, default=False)
@click.option("--format", type=click.STRING, help='json, csv', default='json')
def jobfolders(folder: os.PathLike, output: Optional[str], **options) -> None:
    """Go through a folderstructure recursively and make a list of jobfolder."""
    if isinstance(output, str):
        with open(output, 'w') as filewrapper:
            get_jobfolders(folder, output=filewrapper, **options)
    else:
        get_jobfolders(folder, output=output, **options)


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
def display_converged(folder: os.PathLike) -> None:
    converged_paths = get_jobfolders(folder, 
                                     include=Status.CONVERGED,
                                     without_status=True)

    resultfiles = [x.joinpath('results.traj') for x in converged_paths]
    trajectories = map(ase.io.read, resultfiles)
    ase.visualize.view(trajectories)


if __name__ == '__main__':
    cli()
