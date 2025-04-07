import os
import pathlib

from typing import NamedTuple, Iterator, Any
from jobtool.jobfolders import Status, status_getter


class Result(NamedTuple):
    path: pathlib.Path
    status: Status

    def __repr__(self) -> str:
        return self.path.absolute().as_posix()


def get_walker(folder: os.PathLike, /, lines_checked: int = 20) -> Iterator[Result]:
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
    status = status_getter(strict=True, lines_checked=lines_checked)

    def convert_to_results(jobfolder: pathlib.Path) -> Result:
        return Result(jobfolder, status(jobfolder))

    walker = os.walk(folder)  # type: ignore
    as_path = map(root_as_path, walker)  # Keep only root as a pathlib.Path
    jobfolders_only = filter(is_jobfolder, as_path)  # Filter non-jobfolders out
    return map(convert_to_results, jobfolders_only)


def root_as_path(walk_triplet: tuple[os.PathLike, list[Any], list[Any]]) -> pathlib.Path:
    """Take the argument 'root' from os.walk and convert it to a pathlib.Path and discard the rest of the input arguments"""
    root, *_ = walk_triplet
    return pathlib.Path(root)


def is_jobfolder(path: pathlib.Path) -> bool:
    """A job folder is a directory that includes an "initial.traj" file"""
    return path.joinpath('initial.traj').exists()
