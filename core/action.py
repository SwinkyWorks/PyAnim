from typing import Any, Callable
from types import TracebackType


class Action:
    def __init__(self, input_types: list[type | Any] | type | Any | None = None, return_type: type | Any | None = None) -> None:
        self._actions: list[Callable] = []
        self._input_types: list[type | Any] = [input_types] if isinstance(input_types, type) else [
            Any] if input_types == Any else [] if input_types == None else input_types
        self._return_type: type | Any | None = return_type

    def __iadd__(self, other: Callable):
        self._actions.append(other)
        return self

    def __isub__(self, other: Callable):
        try:
            self._actions.remove(other)
        except ValueError as e:
            e.args = ("Action -= x: x not in Action",)
            e.with_traceback(None)
            raise
        return self

    def __contains__(self, item: object):
        return bool(item in self._actions)

    def __call__(self, *args: Any, **kwds: Any) -> list[Any]:
        return_values = []
        for action in self._actions:
            try:
                return_values.append(action(*args, **kwds))
            except RecursionError as e:
                e.add_note(
                    f"This exception ran within an Action. As this is a RecursionError, expected input and return type arguments are not able to be provided.")
                raise
            except BaseException as e:
                e.add_note(
                    f"This exception ran within an Action. Expected input types are {f"`{self._input_types}`" if len(self._input_types) != 0 else "none or not provided"}; expected return type is {f"`{self._return_type}`" if self._return_type != None else "not provided"}.")
                raise
        return return_values
