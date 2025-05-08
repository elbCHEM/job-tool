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
import sys
import json
import itertools

from jobtool.status import Status
from jobtool.walker import walker, Result
from typing import TextIO, Optional, Literal, Iterator


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
