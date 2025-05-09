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
import pathlib
import operator
import itertools

from jobtool.status import Status
from jobtool.walker import walker, Result
from typing import Optional, Literal, Iterator, Sequence, Callable, overload


@overload
def get_jobfolders(
        folder: os.PathLike,
        /,
        include: Optional[Sequence[Status | str]],
        exclude: Optional[Sequence[Status | str]],
        lines_checked: int,
        initialfilename: str,
        logfilename: str,
        with_status: Literal[True],
) -> Iterator[Result]:
    ...


@overload
def get_jobfolders(
        folder: os.PathLike,
        /,
        include: Optional[Sequence[Status | str]],
        exclude: Optional[Sequence[Status | str]],
        lines_checked: int,
        initialfilename: str,
        logfilename: str,
        with_status: Literal[False],
) -> Iterator[pathlib.Path]:
    ...


def get_jobfolders(
        folder: os.PathLike,
        /,
        include: Optional[Sequence[Status | str]] = None,  # Add finished later
        exclude: Optional[Sequence[Status | str]] = None,  # Add finished later
        lines_checked: int = 20,
        initialfilename: str = 'initial.traj',
        logfilename: str = 'log.txt',
        with_status: bool = False,
        **_,
) -> Iterator[pathlib.Path] | Iterator[Result]:
    results = walker(folder, lines_checked, initialfilename, logfilename)

    # Apply filters to the walker
    if include:
        results = filter(_filter_func(include), results)
    if exclude:
        results = itertools.filterfalse(_filter_func(exclude), results)

    return results if with_status else map(operator.itemgetter('path'), results)


# To-Do: Add 'finished' option for input
def _filter_func(statuses: Sequence[Status | str]) -> Callable[[Result], bool]:
    set_of_statuses = set(map(Status.from_string, statuses))

    def func(result: Result) -> bool:
        return result.status in set_of_statuses

    return func


@overload
def format_jobfolder_results(
    results: Iterator[pathlib.Path | Result],
    format: Literal['csv']
) -> Iterator[str]: ...


@overload
def format_jobfolder_results(
    results: Iterator[pathlib.Path | Result],
    format: Literal['json']
) -> Iterator[dict[str, str]]: ...


def format_jobfolder_results(
        results: Iterator[pathlib.Path | Result],
        format: Literal['csv', 'json']
) -> Iterator[str] | Iterator[dict[str, str]]:
    if format == 'json':
        return map(json_formatter, results)
    if format == 'csv':
        return map(csv_formatter, results)
    raise ValueError(f"Unable to handle formal {format}")


def json_formatter(result: pathlib.Path | Result) -> dict[str, str]:
    if isinstance(result, pathlib.Path):
        return {'path': result.absolute().as_posix()}
    if isinstance(result, Result):
        return {
            'path': result.path.absolute().as_posix(),
            'status': result.status.value,
        }
    raise TypeError(f'Invaid type of result: {type(result)}')


def csv_formatter(result: pathlib.Path | Result) -> str:
    if isinstance(result, pathlib.Path):
        return f"{result.absolute().as_posix()}\n"
    if isinstance(result, Result):
        return f"{result.status.value}, {result.path.absolute().as_posix()}\n"
    raise TypeError(f'Invaid type of result: {type(result)}')
