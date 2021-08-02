import numpy as np


def split_int(x: int, n: int):
    a = np.full(n, x // n)
    a[:x % n] += 1
    return a
