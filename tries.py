"""
Generates table 1.

It uses a bisection method to find the value close to the
probability. There is probably a mathematical way to
find it, but this is, indeed, a way.
"""

import scipy
import numpy as np


def prob_clean(tries, tau=100_000, k=1024):
    """
    p(n, k, tau), ref{eq:prob-multiple-attack}
    """
    return (
        2 * (scipy.stats.norm.cdf(0.5 * np.sqrt(2 * tries / np.float64(tau))) - 0.5)
    ) ** k


def bisection(v, start, end, tries, f):
    """
    bisection method.
    """
    assert f(start) <= v <= f(end)
    assert tries > 1
    for _ in range(tries):
        mid_point = (start + end) / 2
        v2 = f(mid_point)
        if v2 <= v:
            start = mid_point
        else:
            end = mid_point
    return (start + end) / 2


if __name__ == "__main__":
    end = 13_752_561  # prob is 1
    print(bisection(0.5, 10, end, 100, prob_clean))
    print(bisection(0.9, 10, end, 100, prob_clean))
    print(bisection(0.95, 10, end, 100, prob_clean))
    print(bisection(0.99, 10, end, 100, prob_clean))
    print(bisection(0.999, 10, end, 100, prob_clean))
