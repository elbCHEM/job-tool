import json
from typing import TextIO, Iterator


def write_results_json(fp: TextIO, results: Iterator[dict], _) -> None:
    json.dump(list(results), fp, indent=2)


def write_results_csv(fp: TextIO, results: Iterator[str], with_status: bool = True) -> None:
    fp.write('path, status\n' if with_status else 'path\n')
    fp.writelines(results)
