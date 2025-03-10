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
from typing import TypedDict, Unpack, TextIO, Optional, Literal, NamedTuple, Iterator


class Status(enum.StrEnum):
    UNKNOWN = enum.auto()
    NOT_STARTED = enum.auto()
    UNFISHINED = enum.auto()

    NOT_CONVERGED = enum.auto()
    CONVERGED = enum.auto()


class Options(TypedDict):
    output: Optional[TextIO]
    include: Optional[set[Status]]
    exclude: Optional[set[Status]]
    lines_checked: Optional[int]
    without_status: bool
    format: Optional[Literal['csv', 'json']]
    returned: bool


class Result(NamedTuple):
    path: pathlib.Path
    status: Status

    def asjson(self) -> dict:
        return {
            'path': self.path.absolute().as_posix(),
            'status': self.status.name,
        }

    def __str__(self) -> str:
        return f"{self.path.absolute().as_posix()}, {self.status.name}"


CONVERGED_SIGNAL = re.compile('^Date:')
NOT_CONVERGED_SIGNAL = re.compile(r'^Did not converge!\s*$')


def get_jobfolders(folder: os.PathLike, **options: Unpack[Options]) -> Optional[list[Result]]:
    """Go through a folderstructure recursively and make a list of jobfolder.

    Arguments:
        folder (os.PathLike): Root folder of the search

    Options:
        output (TextIO): Location where results are saved. (Default is sys.stdout)
        include (None | list[Status]): If not None, include only these statues in the results. Default is None.
        exclude (None | list[Status]): If not None, the provided statuses are filtered from results. Default is None.

    Returns:
        None | Results: ...
    """
    out = options.get('output', None) or sys.stdout
    format = options.get('format', None)

    # Generate walker gets status of all job folders
    results = walker(folder, **options)

    # Apply filters to the walker
    if (exclude := options.get('exclude', None)):
        results = itertools.filterfalse(lambda result: result.status in exclude, results)
    if (include := options.get('include', None)):
        results = filter(lambda result: result.status in include, results)
    if options.get('without_status', False):
        if format == 'json':
            raise ValueError('Cannot print to json when without_status is given')
        results = map(lambda x: x.path, results)

    # Output results
    if options.get('returned', False) or format is None:
        return list(results)

    if format == 'json':
        json.dump([result.asjson() for result in results], out, indent=4)
    elif format == 'csv':
        for result in results:
            out.write(str(result) + '\n')
        out.writelines(map(str, results))
    else:
        raise ValueError(f"Unable to handle formal {format}")

    return None


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


def is_jobfolder(path: pathlib.Path) -> bool:
    """A job folder is a directory that includes an "initial.traj" file"""
    return path.joinpath('initial.traj').exists()
