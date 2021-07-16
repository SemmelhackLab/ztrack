from abc import ABC, abstractmethod


class Variable(ABC):
    def __init__(self, display_name: str):
        self._display_name = display_name

    @property
    def display_name(self):
        return self._display_name

    @property
    @abstractmethod
    def value(self):
        pass

    @value.setter
    def value(self, value):
        pass


class Numerical(Variable, ABC):
    def __init__(self, display_name: str, value):
        super().__init__(display_name)
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Bounded(Numerical, ABC):
    def __init__(self, display_name: str, value, minimum, maximum):
        super().__init__(display_name, value)
        assert minimum <= value <= maximum
        self._minimum = minimum
        self._maximum = maximum

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value):
        assert self._minimum <= value <= self._maximum
        self._value = value

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum


class Int(Bounded):
    def __init__(self, display_name: str, value: int, minimum: int, maximum: int):
        super().__init__(display_name, value, minimum, maximum)


class UInt8(Int):
    def __init__(self, display_name: str, value: int):
        super().__init__(display_name, value, 0, 255)


class Float(Bounded):
    def __init__(self, display_name: str, value: float, minimum: float, maximum: float, step: float):
        super().__init__(display_name, value, minimum, maximum)
        self._step = step

    @property
    def step(self):
        return self._step
