"""
A jobfolder is a directory that has the structure
|- .
|- ..
|- initial.traj    (Required)
|- log.txt         (optional)
|- results.traj    (optional)
|-     :           (optional)
"""
import pathlib
import itertools

from jobtool.status import Status
from jobtool.walker import walker, Result
from typing import Callable, Iterator, Optional, Sequence


StatusLike = str | Status


def get_jobfolders(
        folder: str | pathlib.Path,
        /,
        include: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        exclude: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        lines_checked: int = 20,
        initialfilename: str = 'initial.traj',
        logfilename: str = 'log.txt',
        **_,
) -> Iterator[Result]:
    results = walker(pathlib.Path(folder), lines_checked, initialfilename, logfilename)

    # Apply filters to the walker
    if include:
        results = filter(filter_func(include), results)
    if exclude:
        results = itertools.filterfalse(filter_func(exclude), results)

    return results


def status_count(
    folder: str | pathlib.Path,
    /,
    lines_checked: int = 20,
    initialfilename: str = 'initial.traj',
    logfilename: str = 'log.txt',
) -> dict[Status, int]:
    """Make a summary of the statuses of all jobfolders in a directory."""
    status_count: dict[Status, int] = {}
    for _, status in get_jobfolders(folder,
                                    lines_checked=lines_checked,
                                    initialfilename=initialfilename,
                                    logfilename=logfilename
                                    ):
        status_count[status] = status_count.get(status, 0) + 1
    return status_count


# To-Do: Add 'finished' option for input
def filter_func(statuses: StatusLike | Sequence[StatusLike]) -> Callable[[Result], bool]:
    if isinstance(statuses, str | Status):
        set_of_statuses = {Status.from_string(statuses), }
    else:
        set_of_statuses = set(map(Status.from_string, statuses))

    def func(result: Result) -> bool:
        return result.status in set_of_statuses

    return func
