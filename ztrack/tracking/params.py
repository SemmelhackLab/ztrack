from abc import ABC
from typing import List

from ztrack.utils.variable import Variable


class Params(ABC):
    def __setattr__(self, name: str, value):
        if isinstance(value, Variable):
            self._parameter_names.append(name)
            self._parameter_list.append(value)
            object.__setattr__(self, name, value)
        elif hasattr(self, name) and isinstance(
            object.__getattribute__(self, name), Variable
        ):
            object.__getattribute__(self, name).value = value
        else:
            object.__setattr__(self, name, value)

    def __getattribute__(self, name: str):
        if isinstance(object.__getattribute__(self, name), Variable):
            return object.__getattribute__(self, name).value
        return object.__getattribute__(self, name)

    def __init__(self):
        self._parameter_names = []
        self._parameter_list: List[Variable] = []

    @property
    def parameter_list(self):
        return self._parameter_list

    @property
    def parameter_names(self):
        return self._parameter_names

    def to_dict(self):
        return {
            name: value.value
            for name, value in zip(self._parameter_names, self._parameter_list)
        }
