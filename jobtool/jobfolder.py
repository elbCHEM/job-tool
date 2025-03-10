"""
A jobfolder is a directory that has the structure
|- .
|- ..
|- initial.traj    (Required)
|- log.txt         (optional)
|- results.traj    (optional)
|-     :           (optional)
"""
import re
import os
import sys
import enum
import json
import pathlib
import itertools
from typing import TextIO, Optional, Literal, NamedTuple, Iterator


class Status(enum.StrEnum):
    UNKNOWN = enum.auto()
    NOT_STARTED = enum.auto()
    UNFISHINED = enum.auto()

    NOT_CONVERGED = enum.auto()
    CONVERGED = enum.auto()


class Result(NamedTuple):
    path: pathlib.Path
    status: Status

    @property
    def path_as_str(self) -> str:
        return self.path.absolute().as_posix()


CONVERGED_SIGNAL = re.compile('^Date:')
NOT_CONVERGED_SIGNAL = re.compile(r'^Did not converge!\s*$')


def get_jobfolders(folder: os.PathLike,
                   /,
                   returned: bool = False,
                   exclude: Optional[Iterator[Status | str]] = None,
                   include: Optional[Iterator[Status | str]] = None,
                   output: TextIO = sys.stdout,
                   format: Literal['json', 'csv'] = 'json',
                   without_status: bool = False,
                   lines_checked: int = 20,
                   ) -> Optional[list[Result]]:
    """Generate a list of all the jobfolders in a given directory tree.

    Args:
        folder (os.PathLike): Top of the searched directory tree.
        returned (bool, optional): If True, results are returned. Defaults to False.
        exclude (Optional[Iterator[Status | str]], optional): Statuses excluded from the results list. Defaults to None.
        include (Optional[Iterator[Status | str]], optional): Statuses included from the results list. Defaults to None.
        output (TextIO, optional): File where results are outputted to. Defaults to sys.stdout.
        format (Literal['json';, 'csv], optional): Format of the results list. Defaults to 'json'.
        without_status (bool, optional): If True, statuses are removed from the output. Defaults to False.
        lines_checked (int, optional): Number of lines checked in log file to determine status. Defaults to 20.

    Raises:
        ValueError: If provided format is not accepted

    Returns:
        Optional[list[Result]]: If "returned" flag is on, then list of results are returned. Else None.
    """
    # Generate walker gets status of all job folders
    results = walker(folder, lines_checked)

    # Apply filters to the walker
    if exclude is not None:
        results = itertools.filterfalse(_filter_func(exclude), results)
    if include is not None:
        results = filter(_filter_func(include), results)

    # Output results to output via given format and output method
    if returned:
        return list(results)
    if format == 'json':
        write_as_json(results, output, without_status)
    elif format == 'csv':
        write_to_csv(results, output, without_status)
    else:
        raise ValueError(f"Unable to handle formal {format}")

    return None


def _filter_func(group: Iterator[Status | str]):
    group_as_statuses = set(x if isinstance(x, Status) else Status(x.lower().strip()) for x in group)

    def func(result: Result) -> bool:
        return result.status in group_as_statuses

    return func


def walker(folder: os.PathLike, /, lines_checked: int = 20) -> Iterator[Result]:
    """Generate a walker iterator that walks all the jobfolder in the directory tree.

    Given a folder, the walker iterates all subfolders that are considered as a jobfolder.
    Here, a jobfolder is a folder that includes:
     - An "initial.traj" file. (Required)
     - An "log.txt" file. (Optional)
     - A "results.traj" file. (Optional)

    Args:
        folder (os.PathLike): Topfolder of the walker.
        lines_checked (int, optional): Number of lines checked in the end of the log.txt file to check status. Defaults to 20.

    Yields:
        Iterator[Result]: Iterator that outputs (pathlib.Path, Status) of jobfolders.
    """
    def root_as_path(triplet: tuple[os.PathLike, list[str], list[str]]) -> pathlib.Path:
        root, *_ = triplet
        return pathlib.Path(root)

    def as_results(path: pathlib.Path) -> Result:
        status = get_status(path, lines_checked)
        assert status is not None
        return Result(path, status)

    # [(str, [str], [str])] => [Path] => [JobfolderPaths] => [Results]
    return map(as_results, filter(is_jobfolder, map(root_as_path, os.walk(folder))))  # type: ignore


def get_status(path: pathlib.Path, /, lines_checked: int = 20, **_) -> Optional[Status]:
    """Check if given path is a jobfolder. Returns status if so, else None

    Args:
        path (pathlib.Path): Path is question.
        lines_checked (int, optional): Number of lines that are check at the end of the log file. Defaults to 20.

    Returns:
        Optional[Status]: Status of the job. If path is not a jobfolder, then None is returned.
    """
    if not is_jobfolder(path):
        return None

    # Job is not started if logfile is not existing
    if not (logfile := path.joinpath('log.txt')).exists():
        return Status.NOT_STARTED

    with open(logfile, 'r') as filewrapper:
        lines = filewrapper.readlines()
        if 0 == len(lines):
            return Status.UNKNOWN  # Cannot determine process if log file is empty

    # Something has definetly run. The last lines can determine the result
    last_few_lines = lines[-lines_checked:]

    if CONVERGED_SIGNAL.match(last_few_lines[-1]):
        return Status.CONVERGED
    if any(map(NOT_CONVERGED_SIGNAL.match, last_few_lines)):
        return Status.NOT_CONVERGED

    return Status.UNFISHINED


def write_as_json(results: Iterator[Result], output: TextIO, /, without_status: bool = False) -> None:
    if without_status:
        in_json_format = [{'path': result.path_as_str} for result in results]
    else:
        in_json_format = [{'path': result.path_as_str, 'status': result.status.value} for result in results]

    json.dump(in_json_format, output, indent=4)


def write_to_csv(results: Iterator[Result], output: TextIO, /, without_status: bool = False) -> None:
    if without_status:
        formatter = "{result.status.value}, {result.path_as_str}\n"
    else:
        formatter = "{result.path_as_str}\n"
    for result in results:
        output.write(formatter.format(result=result))


def is_jobfolder(path: pathlib.Path) -> bool:
    """A job folder is a directory that includes an "initial.traj" file"""
    return path.joinpath('initial.traj').exists()
