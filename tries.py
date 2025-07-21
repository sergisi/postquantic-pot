"""
Generates table 1.

It uses a bisection method to find the value close to the
probability. There is probably a mathematical way to
find it, but this is, indeed, a way.
"""

import typer

import scipy
import numpy as np

app = typer.Typer()


def prob_clean(tries, tau=100_000, k=1024):
    """
    p(n, k, tau), ref{eq:prob-multiple-attack}
    """
    return (
        2 * (scipy.stats.norm.cdf(0.5 * np.sqrt(2 * tries / np.float64(tau))) - 0.5)
    ) ** k


def bisection(target, start, end, tries, f):
    """
    bisection method.
    """
    assert f(start) <= target <= f(end)
    assert tries > 1
    for _ in range(tries):
        mid_point = (start + end) / 2
        v2 = f(mid_point)
        if v2 <= target:
            start = mid_point
        else:
            end = mid_point
    return (start + end) / 2


@app.command()
def probability_failure(safe_mask: int = 2000, q: int = 12 * 1024 + 1):
    """
    Get the probability of failure
    """
    from scipy import stats

    p = 1 - 4 * safe_mask / q
    bin = stats.Binomial(n=1024, p=p)
    print(f"p = {p}")
    print("2^{-128} = ", 2 ** (-128))
    print("256 bits de seguretat: ", bin.cdf(256))
    print("128 bits de seguretat: ", bin.cdf(128))


@app.command()
def find_safe_mask(target: float = 2 ** (-128), q: int = 12 * 1024 + 1):
    from scipy import stats

    def f(x):
        p = 1 - 4 * x / q
        bin = stats.Binomial(n=1024, p=p)
        return bin.cdf(256)

    safe_mask = bisection(target, 1, 3000, 128, f)
    print(f"safe_mask = {safe_mask}")


@app.command()
def multiple_attacks():
    end = 13_752_561  # prob is 1
    print(bisection(0.5, 10, end, 100, prob_clean))
    print(bisection(0.9, 10, end, 100, prob_clean))
    print(bisection(0.95, 10, end, 100, prob_clean))
    print(bisection(0.99, 10, end, 100, prob_clean))
    print(bisection(0.999, 10, end, 100, prob_clean))


if __name__ == "__main__":
    app()
