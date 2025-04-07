import itertools

from jobtool.walker import Result
from typing import Optional, Iterator, Iterable, Callable


def apply_filters(walker: Iterator[Result],
                  /,
                  include: Optional[str | Iterable[str]] = None,
                  exclude: Optional[str | Iterable[str]] = None,
                  ) -> Iterator[Result]:
    """Apply filters to the walker such that only jobfolders with given statuses are yeilded

    Args:
        walker (Iterator[Result]): Iterator that yeilds (path, status)-tuples of jobfolders

    Keywords:
        exclude (Iterable[str], optional): Statuses excluded from the results list. Defaults to None.
        include (Iterable[str], optional): Statuses included from the results list. Defaults to None.
    """
    if exclude:
        walker = itertools.filterfalse(check_status_match(exclude), walker)
    if include:
        walker = filter(check_status_match(include), walker)

    return walker


def check_status_match(statuses: str | Iterable[str]) -> Callable[[Result], bool]:
    """Generate a function that check if a given object matches a collection of strings."""
    match statuses:
        case str():
            check_match = homogenize_user_input(statuses).__eq__
        case Iterable():
            check_match = set(homogenize_user_input(x) for x in statuses).__contains__
        case _:
            raise TypeError(f'Cannot handle type of "strings" being {type(statuses)}')

    def check_status(result: Result) -> bool:
        """Check if a walker result has a status equal to one of the provied statuses"""
        return check_match(result.status)

    return check_status


def homogenize_user_input(userstring: str) -> str:
    """Ensures a user input is stripped from spaces and convered to lower case"""
    return userstring.strip().lower()
