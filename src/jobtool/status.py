"""
Jobfolder layerout:
|-- initial.traj    (Required)
|-- <logfile>       (Optional)
|-- results.traj    (Optional)


Possible statuses:
- Converged
- Not converged
- Unfinished
- Not started
- Unknown


Not started
-----------
If the job is not started, then its log file does not exist


Converged
---------
A converged job has a logfile whose last line is formatted as
Date: ...

Not converged
-------------
If a job is finished, but has not converged, then it one of its last lines have the format
Did not converge!

Unfinished
----------
If the jobfolder has a non-empty logfile, but it does not match converged or non-converged
"""
from __future__ import annotations

import re
import enum
import pathlib
from typing import Optional, Literal, overload


class Status(enum.StrEnum):
    UNKNOWN = enum.auto()
    CONVERGED = enum.auto()
    NOT_CONVERGED = enum.auto()
    UNFINISHED = enum.auto()
    NOT_STARTED = enum.auto()

    @staticmethod
    def from_string(string: str) -> Status:
        return Status(string.strip().lower().replace('-', '_'))


CONVERGED_SIGNAL = re.compile('^Date:')
NOT_CONVERGED_SIGNAL = re.compile(r'^Did not converge!\s*$')


@overload
def get_status(
    path: pathlib.Path,
    /,
    lines_checked: int,
    initialfile: str,
    logfilename: str,
    strict: Literal[True],
) -> Status: ...


@overload
def get_status(
    path: pathlib.Path,
    /,
    lines_checked: int,
    initialfile: str,
    logfilename: str,
    strict: Literal[False],
) -> Optional[Status]: ...


def get_status(
        path: pathlib.Path,
        /,
        lines_checked: int = 20,
        initialfile: str = 'initial.traj',
        logfilename: str = 'log.txt',
        strict: bool = False,
        **_
) -> Optional[Status]:
    """Check if given path is a jobfolder. Returns status if so, else None

    Args:
        path (pathlib.Path): Path is question.
        lines_checked (int, optional): Number of lines that are check at the end of the log file. Defaults to 20.

    Returns:
        Optional[Status]: Status of the job. If path is not a jobfolder, then None is returned.
    """
    if not is_jobfolder(path, initialfile):
        if strict:
            raise ValueError("Expected a jobfolder but were not given one - To supress, please set 'strict' to False")
        return None

    # If no log file exists, then calculations are not started
    if not (logfile := path.joinpath(logfilename)).exists():
        return Status.NOT_STARTED

    # Determine status from content of file
    with open(logfile, 'r') as filewrapper:
        if not (lines := filewrapper.readlines()):
            return Status.UNKNOWN  # Cannot determine process if log file is empty
        last_few_lines = lines[-lines_checked:]

    if CONVERGED_SIGNAL.match(last_few_lines[-1]):
        return Status.CONVERGED

    if any(NOT_CONVERGED_SIGNAL.match(line) for line in last_few_lines):
        return Status.NOT_CONVERGED

    return Status.UNFINISHED


def is_jobfolder(path: pathlib.Path, /, initialfilename: str = 'initial.traj') -> bool:
    """A job folder is a directory that includes an "initial.traj" file"""
    return path.joinpath(initialfilename).exists()


def is_finished(status: Status) -> bool:
    return status in {Status.CONVERGED, Status.NOT_CONVERGED}
