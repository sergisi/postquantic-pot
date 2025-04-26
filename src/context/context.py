import typing
import itertools
from sage.all_cmdline import (
    Integer,
    Integers,
    Zp,
    vector,
    sqrt,
)  # import sage library
import math
import numpy as np
import dataclasses as dto
import functools
from ..poly import Poly, PolyVec
import random
from sage.stats.distributions.discrete_gaussian_polynomial import (
    DiscreteGaussianDistributionPolynomialSampler as DisGauss,
)
from .falcon_params import params
from os import urandom


@dto.dataclass
class Context:
    """
    Parameters that get passed down in the function calls.
    """

    p: int
    degree: int
    m: int
    cbd_noise: int
    small_degree: int
    small_max_value: int
    rej_sampling_module: int
    # NOTE: s_param = cbd_noise,
    # e1_param and e2_param exist
    e1_param: int
    e2_param: int

    @functools.cached_property
    def salt(self) -> bytes:
        return urandom(40)  # 40 bytes of randomness

    @functools.cached_property
    def rej_sampling_s(self):
        return 0.675 * 2 * self.degree * (self.rej_sampling_module)

    @functools.cached_property
    def rej_sampling_bound(self):
        return max(
            self.rej_sampling_s * sqrt(2 * self.degree), params[self.degree].sig_bound
        )

    def update(self, **kwargs) -> "Context":
        return Context(**(dto.asdict(self) | kwargs))

    @property
    def len_bits(self):
        return math.ceil(math.log2(self.p))

    @functools.cached_property
    def Zp(self):
        return Integers(self.p)

    @functools.cached_property
    def Zpx(self):
        return self.Zp["x"]

    @functools.cached_property
    def x(self):
        (x,) = self.Zpx._first_ngens(1)
        return x

    @functools.cached_property
    def ZpxQ(self):
        return self.Zpx.quotient(self.x**self.degree + Integer(1), "X")

    def rand_function(self):
        return Zp(random.randint(-self.small_max_value, self.small_max_value - 1))

    def cbd(self, n: int):
        return random.binomialvariate(n, 0.5) - random.binomialvariate(n, 0.5)

    def random_element(self):
        return self.ZpxQ(
            [self.Zp(random.randint(0, self.p - 1)) for _ in range(self.degree)]
        )

    def random_vector(self, size: int | None = None, like: PolyVec | None = None):
        if size is None:
            size = self.m
        if like != None:
            size = len(like)
        return vector(
            [self.random_element() for _ in range(size)], self.ZpxQ, immutable=True
        )

    ##########################

    def random_element_small(
        self,
        rand_function: typing.Callable[[], int] | None = None,
    ):
        if rand_function is None:
            rand_function = self.rand_function
        return self.ZpxQ([rand_function() for _ in range(self.small_degree + 1)])

    def random_vector_small(
        self,
        size: int | None = None,
        rand_element: typing.Callable[[], int] | None = None,
    ):
        if size is None:
            size = self.m
        if rand_element is None:
            rand_element = lambda: self.random_element_small()
        return vector([rand_element() for _ in range(size)], self.ZpxQ, immutable=True)

    @functools.cached_property
    def get_gauss(self) -> typing.Callable[[int], typing.Callable[[], int]]:
        @functools.lru_cache()
        def get_gauss(n: int) -> int:
            return DisGauss(self.ZpxQ, self.degree, sigma=sqrt(n / 2))

        return get_gauss

    def r_small(self, n: int | None = None):
        """
        The purpose of this function is to change easily the
        type of random that the protocol uses.
        """
        if n is None:
            n = self.cbd_noise
        if n > 30:
            return self.get_gauss(n)()
        return self.random_element_small(rand_function=lambda: self.cbd(n))

    def r_small_vector(
        self, n: int | None = None, like: PolyVec | None = None
    ) -> PolyVec:
        if n is None:
            n = self.m
        if like != None:
            size = len(like)
        else:
            size = self.m
        return self.random_vector_small(size=size, rand_element=lambda: self.r_small(n))

    def collapse_even_gen(self, v) -> typing.Generator[int, None, None]:
        p2 = self.p // 2
        m2 = (int(c) if int(c) <= p2 else int(c) - self.p for c in v)
        return (int(c) for c in m2)

    def collapse_even(self, v) -> list[int]:
        return list(self.collapse_even_gen(v))

    def collapse(self, v):
        """In this protocol, it is based on the second
        subgroup q."""
        try:
            w = v[0][0]
            v = w
        except:
            pass
        q2 = self.p // 2
        v1 = (int(coef) % self.p for coef in v)
        v2 = (coef if coef < q2 else self.p - coef for coef in v1)
        q4 = q2 // 2
        v3 = (0 if coef < q4 else 1 for coef in v2)
        return tuple(v3)

    def get_mask_of_element(self, v):
        p = self.p
        q2 = p // 2
        v1 = (int(coef) % p for coef in v)
        v2 = (coef if coef < q2 else p - coef for coef in v1)
        q4 = q2 // 2
        v3 = (abs(coef - q4) for coef in v2)
        v4 = ((c, i) for i, c in enumerate(v3))
        v5 = list(filter(lambda x: x[0] > 2000, v4))
        res = random.sample(v5, k=self.degree // 4)
        # gotta_go_fast breaks if not
        # but on normal executions it will still be 256
        res = [i for _, i in res]
        res = sorted(res)
        return res

    def apply_mask(self, ls, mask):
        return sum(x * 2**i for x, i in enumerate(ls[i] for i in mask))

    def _to_array(self, vs: PolyVec):
        return np.array(
            list(itertools.chain.from_iterable(self.collapse_even(v) for v in vs)),
            dtype=np.int32,
        )

    def norm(self, z: PolyVec):
        return np.linalg.norm(self._to_array(z))
