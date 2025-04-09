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
import pathlib


from jobtool.filters import apply_filters
from jobtool.walker import get_walker, Result

from typing import Iterable, Iterator, TextIO, Literal, Optional, Any


def get_jobfolders(folder: os.PathLike,
                   /,
                   with_status: bool = True,
                   output: TextIO = sys.stdout,
                   format: Literal['json', 'csv', 'none'] = 'csv',
                   lines_checked: Optional[int] = None,
                   include: Optional[str | Iterable[str]] = None,
                   exclude: Optional[str | Iterable[str]] = None,
                   **_: Any,  # Deprecated keywords
                   ) -> list[pathlib.Path] | list[Result]:
    walker = get_walker(folder, lines_checked)  # Generate walker gets status of all job folders
    walker = apply_filters(walker, include, exclude)  # Apply filters to the walker

    # Output results to output via given format and output method
    match format:
        case 'none':
            results = list(walker)
        case 'json':
            results = write_as_json(walker, output, with_status)
        case 'csv':
            results = write_to_csv(walker, output, with_status)
        case _:
            raise ValueError(f"Unable to handle formal {format}")

    if not with_status:
        return [path for path, _ in results]
    return results


def write_as_json(walker: Iterator[Result], output: TextIO, /, with_status: bool = True) -> list[Result]:
    if with_status:
        def format_json(result: Result) -> dict[str, str]:
            return {
                'path': result.path.absolute().as_posix(),
                'status': result.status.value,
            }
    else:
        def format_json(result: Result) -> dict[str, str]:
            return {
                'path': result.path.absolute().as_posix(),
            }

    results: list[Result] = []
    as_json: list[dict[str, str]] = []
    for result in walker:
        results.append(result)
        as_json.append(format_json(result))

    json.dump(as_json, output, indent=2)
    return results


def write_to_csv(walker: Iterator[Result], output: TextIO, /, with_status: bool = True) -> list[Result]:
    if with_status:
        header = "path, status\n"
        def formatter(result: Result) -> str:
            return f"{result.path.absolute().as_posix()}, {result.status.value}\n"
    else:
        header = "path\n"
        def formatter(result: Result) -> str:
            return f"{result.path.absolute().as_posix()}\n"

    lines: list[str] = [header]
    results: list[Result] = []
    for result in walker:
        results.append(result)
        lines.append(formatter(result))
    
    output.writelines(lines)
    return results
