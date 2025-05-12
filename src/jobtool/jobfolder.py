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
import json
import pathlib
import operator
import itertools

from jobtool.status import Status
from jobtool.walker import walker, Result
from typing import TextIO, Optional, Literal, Iterator, Sequence, Callable, overload


StatusLike = str | Status


@overload
def get_jobfolders(
        folder: os.PathLike,
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
        folder: os.PathLike,
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
        folder: os.PathLike,
        /,
        include: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        exclude: Optional[StatusLike | Sequence[StatusLike]] = None,  # Add finished later
        lines_checked: int = 20,
        initialfilename: str = 'initial.traj',
        logfilename: str = 'log.txt',
        with_status: bool = True,
        **_,
) -> Iterator[pathlib.Path] | Iterator[Result]:
    results = walker(folder, lines_checked, initialfilename, logfilename)

    # Apply filters to the walker
    if include:
        results = filter(_filter_func(include), results)
    if exclude:
        results = itertools.filterfalse(_filter_func(exclude), results)

    return results if with_status else map(operator.itemgetter(0), results)


# To-Do: Add 'finished' option for input
def _filter_func(statuses: StatusLike | Sequence[StatusLike]) -> Callable[[Result], bool]:
    if isinstance(statuses, StatusLike):
        set_of_statuses = {Status.from_string(statuses), }
    else:
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


@overload
def write_results(fp: TextIO, result: Iterator[str], format: Literal['csv'], with_status: bool) -> None: ...


@overload
def write_results(fp: TextIO, result: Iterator[dict], format: Literal['json'], with_status: bool) -> None: ...


def write_results(
        fp: TextIO,
        results: Iterator[str] | Iterator[dict],
        format: Literal['csv', 'json'],
        with_status: bool = True,
) -> None:
    match format:
        case 'json':
            json.dump(list(results), fp, indent=2)
        case 'csv':
            fp.write('path, status\n' if with_status else 'path\n')
            fp.writelines(results)
        case _:
            raise ValueError(f'Unknown {format=}')
