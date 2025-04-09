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
import enum
import pathlib
import functools

from typing import Callable, Optional


class Status(enum.StrEnum):
    UNKNOWN = enum.auto()
    UNFISHINED = enum.auto()
    NOT_STARTED = enum.auto()

    CONVERGED = enum.auto()
    EMPTY_LOG_FILE = enum.auto()
    DID_NOT_CONVERGED = enum.auto()
    NOT_A_JOBFOLDER = enum.auto()


DEFAULT_LINES_CHECKED = 20
CONVERGED_SIGNAL = re.compile('^Date:')
NOT_CONVERGED_SIGNAL = re.compile(r'^Did not converge!\s*$')


def get_status(jobfolder: pathlib.Path, /, lines_checked: int = DEFAULT_LINES_CHECKED) -> Status:
    """Get status of a given jobfolder.

    Args:
        jobfolder (pathlib.Path): Jobfolder in question as a Path object
        lines_checked (int, optional): Number of lines check when determining job status. Defaults to DEFAULT_LINES_CHECKED.

    Returns:
        Status: Status of the jobfolder in question.
    """
    if not is_jobfolder(jobfolder):
        return Status.NOT_A_JOBFOLDER

    if not (logfile := jobfolder.joinpath('log.txt')).exists():
        return Status.NOT_STARTED

    # Read log-file and determine status
    with open(logfile, 'r') as filewrapper:
        if not (lines := filewrapper.readlines()):
            return Status.EMPTY_LOG_FILE
    last_few_lines = lines[-lines_checked:]

    # Determine convergence from last few lines
    if CONVERGED_SIGNAL.match(last_few_lines[-1]):
        return Status.CONVERGED
    if any(NOT_CONVERGED_SIGNAL.match(line) for line in last_few_lines):
        return Status.DID_NOT_CONVERGED

    return Status.UNFISHINED


def status_getter(strict: bool = False,
                  lines_checked: Optional[int] = DEFAULT_LINES_CHECKED
                  ) -> Callable[[pathlib.Path], Status]:
    lines_checked = lines_checked or DEFAULT_LINES_CHECKED

    if not strict:
        return functools.partial(get_status, lines_checked=lines_checked)

    def getter(path: pathlib.Path) -> Status:
        if (status := get_status(path, lines_checked)) is Status.NOT_A_JOBFOLDER:
            raise ValueError('Provided folder is not a jobfolder. To supress exception, use strict=False')
        return status

    return getter


def is_jobfolder(path: pathlib.Path) -> bool:
    """A job folder is a directory that includes an "initial.traj" file"""
    return path.joinpath('initial.traj').exists()
