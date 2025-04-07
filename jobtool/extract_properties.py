import os
import ase
import ase.io
import pathlib
from typing import Optional, Callable, overload, Any


PREDEFINED_EXTRACTORS: dict[str, Callable[[ase.Atoms], Any]] = {
    'self': lambda x: x,
    'cell': ase.Atoms.get_cell,

    'a': lambda atoms: atoms.get_cell().lengths()[0],
    'b': lambda atoms: atoms.get_cell().lengths()[1],
    'c': lambda atoms: atoms.get_cell().lengths()[2],

    'symbols': ase.Atoms.get_chemical_symbols,
    'energy': ase.Atoms.get_potential_energy,
    'magmom': ase.Atoms.get_magnetic_moments,
}


class ExtractorMap(dict[str, Callable[[ase.Atoms], Any]]):

    def __init__(self,
                 predefined: tuple[str] | tuple[()] = (),
                 *args: str,
                 __map: Optional[dict[str, Callable[[ase.Atoms], Any]]] = None,
                 **kwargs: Callable[[ase.Atoms], Any],
                 ) -> None:
        super().__init__()

        if (from_string := tuple(predefined) + args):
            for property in from_string:
                self.add(property)
        if (from_dict := (__map or {}) | kwargs):
            for key, func in from_dict.items():
                self.add(key, func)

    @overload
    def add(self, key: str) -> None: ...
    @overload
    def add(self, key: str, func: Callable[[ase.Atoms], Any]) -> None: ...

    def add(self, key: str, func: Optional[Callable[[ase.Atoms], Any]] = None) -> None:
        if func is not None:
            self[key] = func
            return
        if key not in PREDEFINED_EXTRACTORS:
            raise NotImplementedError(f'{property=} is not defined')
        self[key] = PREDEFINED_EXTRACTORS[key]

    def remove(self, key: str) -> None:
        self[key]

    @overload
    def __call__(self, __input: ase.Atoms) -> dict[str, Any]: ...
    @overload
    def __call__(self, __input: pathlib.Path) -> dict[str, Any]: ...

    def __call__(self, __input: ase.Atoms | pathlib.Path) -> dict[str, Any]:
        match __input:
            case ase.Atoms():
                atoms = __input
            case os.PathLike():
                if isinstance(atoms := ase.io.read(__input, index='-1'), ase.Atoms):  # type: ignore
                    return self.__call__(atoms)
                raise NotImplementedError('Support for multiple images is not implements yet')
            case _:
                raise TypeError(f"Cannot handle {type(__input)=}")

        return {
            key: func(atoms)
            for key, func in self.items()
        }
