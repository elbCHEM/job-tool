import pathlib
from jobtool.jobfolder import Result


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
