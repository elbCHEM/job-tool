"""
A jobfolder is a directory that has the structure
|- .
|- ..
|- initial.traj    (Required)
|- log.txt         (optional)
|- results.traj    (optional)
|-     :           (optional)
"""
import sys
import click
import pathlib

import ase
import ase.io
import ase.visualize
from typing import TextIO, Literal, Optional, Any

import jobtool.write as writers
import jobtool.format as formatters

from jobtool.status import Status
from jobtool.walker import walker
from jobtool.jobfolder import get_jobfolders


@click.group()
@click.option('-o', '--output', type=click.Path(dir_okay=False, path_type=pathlib.Path), help='Output file. Default is stdout')
@click.option('--lines_checked', type=click.IntRange(min=0), help='Number of lines check in the end of the line')
@click.option('--initialfilename', type=click.STRING, help='Name of initial files')
@click.option('--logfilename', type=click.STRING, help='Name of log files')
@click.pass_context
def cli(
    ctx: click.Context,
    output: Optional[pathlib.Path],
    lines_checked: int,
    initialfilename: str,
    logfilename: str,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj['output'] = output
    ctx.obj['lines_checked'] = lines_checked
    ctx.obj['initialfilename'] = initialfilename
    ctx.obj['logfilename'] = logfilename


@cli.command()
@click.pass_context
@click.option('--remove-none', is_flag=True, help='Remove all arguments that was not provided')
def check_args(ctx: click.Context, remove_none: bool) -> None:
    """Outputs CLI context options - Mostly used for debugging"""
    if remove_none:
        options = {name: val for name, val in ctx.obj.items() if val is not None}
    else:
        options = ctx.obj
    print(options)


@cli.command()
def get_status_list() -> None:
    """Print all valid status values"""
    click.echo("Valid statuses:")
    click.echo("--------------")
    for status in Status:
        click.echo(f"- {status.value}")


@cli.command()
@click.argument('folder', default='.', type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path))
@click.option('--include', type=click.STRING, multiple=True, help='Statusses included in the list')
@click.option('--exclude', type=click.STRING, multiple=True, help='Statusses excluded from the list')
@click.option('--format', default='json', type=click.STRING, help='Format of the output')
@click.option('--without_status', is_flag=True, help='If True, the status is dropped')
@click.pass_context
def jobfolders(
    ctx: click.Context,
    folder: pathlib.Path,
    include: Optional[list[str]],
    exclude: Optional[list[str]],
    format: Literal['csv', 'json'],
    without_status: bool,
) -> None:
    options = remove_none_provided_options(ctx.obj)

    results = get_jobfolders(folder, include, exclude, with_status=True, **options)

    match format:
        case 'csv':
            def writer(out: TextIO) -> None:
                __formatted = map(formatters.csv_formatter, results)
                writers.write_results_csv(out, __formatted, with_status=not without_status)
        case 'json':
            def writer(out: TextIO) -> None:
                __formatted = map(formatters.json_formatter, results)
                writers.write_results_json(out, __formatted, not without_status)

    if 'output' not in options:
        writer(sys.stdout)
    else:
        with open(options['output'], 'w') as filewrapper:
            writer(filewrapper)


@cli.command()
@click.argument("folder", default='.', type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path))
@click.pass_context
def display_converged(ctx: click.Context, folder: pathlib.Path) -> None:
    options = remove_none_provided_options(ctx.obj)

    structures = []
    for path, _ in get_jobfolders(folder, include='converged', **options):
        structures.append(ase.io.read(path.joinpath('results.traj')))

    if not structures:
        click.echo(f"No converged jobs in folder {folder}")
        return
    ase.visualize.view(structures)


@cli.command()
@click.argument("folder", default='.',  type=click.Path(exists=True, file_okay=False))
@click.pass_context
def count_statuses(ctx: click.Context, folder: pathlib.Path) -> None:
    options = remove_none_provided_options(ctx.obj)

    # Count jobfolders in directory
    count: dict[Status, int] = {}
    for _, status in walker(folder, **options):
        count[status] = count.get(status, 0) + 1

    # Print to the user
    click.echo("Count of jobfolders with status")
    click.echo("===============================")
    for status, __count in count.items():
        click.echo(f"{status}: {__count}")
    click.echo("-------------------------------")
    click.echo(f"Total: {sum(count.values())}")


def remove_none_provided_options(options: dict) -> dict[str, Any]:
    return {key: val for key, val in options.items() if val is not None}


if __name__ == '__main__':
    cli()
