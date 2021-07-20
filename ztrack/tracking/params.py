from abc import ABC
from typing import List

from ztrack.utils.variable import Variable


class Params(ABC):
    def __setattr__(self, name: str, value):
        if isinstance(value, Variable):
            self._parameter_names.append(name)
            self._parameter_list.append(value)
            has_attr = False
            attr = None
            if hasattr(self, name):
                has_attr = True
                attr = object.__getattribute__(self, name)
            object.__setattr__(self, name, value)
            if has_attr:
                self.__setattr__(name, attr)
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

    def __init__(self, params: dict = None):
        self._parameter_names = []
        self._parameter_list: List[Variable] = []
        if params is not None:
            self._set_params(params)

    def _set_params(self, params: dict):
        for key, value in params.items():
            self.__setattr__(key, value)

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
