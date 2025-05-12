import os
import pathlib
import operator
import functools

from typing import NamedTuple, Iterator
from jobtool.status import Status, get_status, is_jobfolder


class Result(NamedTuple):
    path: pathlib.Path
    status: Status


def walker(
        folder: os.PathLike,
        /,
        lines_checked: int = 20,
        initialfilename: str = 'initial.traj',
        logfilename: str = 'log.txt',
        ) -> Iterator[Result]:
    """Generate a walker iterator that walks all the jobfolder in the directory tree.

    Given a folder, the walker iterates all subfolders that are considered as a jobfolder.
    Here, a jobfolder is a folder that includes:
     - An "initial.traj" file. (Required)
     - An "log.txt" file. (Optional)
     - A "results.traj" file. (Optional)

    :param (os.PathLike) folder: Topfolder of the walker.
    :param (int, optional) lines_checked: Lines checked in the end of the log file when checking status. Defaults to 20.
    :param (str, optional) initialfilename: Name of initial file. Default is 'initial.traj'.
    :param (str, optional) logfilename: Name of logfiles. Default is 'log.txt'

    Yields:
        Iterator[Result]: Iterator that outputs (pathlib.Path, Status) of jobfolders.
    """
    directory_walker = os.walk(folder)  # type: ignore[type-var]
    roots = map(pathlib.Path, map(operator.itemgetter(0), directory_walker))
    jobfolders = filter(functools.partial(is_jobfolder, initialfilename=initialfilename), roots)

    def as_result(jobfolder: pathlib.Path) -> Result:
        status = get_status(jobfolder,
                            lines_checked=lines_checked,
                            initialfile=initialfilename,
                            logfilename=logfilename,
                            strict=True
                            )
        return Result(jobfolder, status)

    return map(as_result, jobfolders)
