"""
Hypothesis that r_small(1_000_000) is
super costly.


Hypothesis that r_small(n > 30), specially n = 1_000_000,
with a GaussDistribution would be super fast
"""

import random
import timeit
import math


def hypothesis():
    return random.binomialvariate(1_000_000, 0.5) - random.binomialvariate(
        1_000_000, 0.5
    )


def hypothesis2():
    return int(random.gauss(sigma=math.sqrt(1_000_000 / 2)))


if __name__ == "__main__":
    t = timeit.timeit(
        "hypothesis()", setup="from __main__ import hypothesis", number=10_000
    )
    print(t)
    t = timeit.timeit(
        "hypothesis2()", setup="from __main__ import hypothesis2", number=10_000
    )
    print(t)
