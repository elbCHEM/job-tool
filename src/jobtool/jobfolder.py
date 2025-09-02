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
import operator
import itertools

from jobtool.status import Status
from jobtool.walker import walker, Result
from typing import Callable, Iterator, Literal, Optional, Sequence, overload


type StatusLike = str | Status


@overload
def get_jobfolders(
        folder: str | pathlib.Path,
        /,
        include: Optional[StatusLike | Sequence[StatusLike]],
        exclude: Optional[StatusLike | Sequence[StatusLike]],
        lines_checked: int,
        initialfilename: str,
        logfilename: str,
        with_status: Literal[True],
) -> Iterator[Result]:
    ...


@overload
def get_jobfolders(
        folder: str | pathlib.Path,
        /,
        include: Optional[StatusLike | Sequence[StatusLike]],
        exclude: Optional[StatusLike | Sequence[StatusLike]],
        lines_checked: int,
        initialfilename: str,
        logfilename: str,
        with_status: Literal[False],
) -> Iterator[pathlib.Path]:
    ...


def get_jobfolders(
        folder: str | pathlib.Path,
        /,
        include: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        exclude: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        lines_checked: int = 20,
        initialfilename: str = 'initial.traj',
        logfilename: str = 'log.txt',
        with_status: bool = True,
        **_,
) -> Iterator[pathlib.Path] | Iterator[Result]:
    results = walker(pathlib.Path(folder), lines_checked, initialfilename, logfilename)

    # Apply filters to the walker
    if include:
        results = filter(filter_func(include), results)
    if exclude:
        results = itertools.filterfalse(filter_func(exclude), results)

    return results if with_status else map(operator.itemgetter(0), results)


# To-Do: Add 'finished' option for input
def filter_func(statuses: StatusLike | Sequence[StatusLike]) -> Callable[[Result], bool]:
    if isinstance(statuses, str | Status):
        set_of_statuses = {Status.from_string(statuses), }
    else:
        set_of_statuses = set(map(Status.from_string, statuses))

    def func(result: Result) -> bool:
        return result.status in set_of_statuses

    return func
