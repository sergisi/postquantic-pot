import typing
import functools as fun
import itertools as it
from sage.all_cmdline import (
    Integer,
    Integers,
    Zp,
    vector,
    sqrt,
    matrix,
    randint,
    set_random_seed
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



def seeded_function(f):
    @fun.wraps(f)
    def wrapper(*args, seed: int | None = None, **kwargs):
        if seed is None:
            return f(*args, **kwargs)
        set_random_seed(seed)
        res = f(*args, **kwargs)
        set_random_seed()  # NOTE: Reset state
        return res

    return wrapper




@dto.dataclass
class AssymetricExtra:
    e1_param: int
    e2_param: int


@dto.dataclass
class Context[T]:
    """
    Space where the falcon and the blind signature work.

    """

    q: int
    degree: int
    k: int
    l: int
    cbd_noise: int
    rej_sampling_module: int
    safe_mask: int
    more: T

    @functools.cached_property
    def salt(self) -> bytes:
        return urandom(40)  # 40 bytes of randomness

    @functools.cached_property
    def rej_sampling_s(self):
        return 0.675 * 2 * self.degree * (self.rej_sampling_module)

    @functools.cached_property
    def rej_sampling_bound(self):
        return max(
            self.rej_sampling_s * math.sqrt(2 * self.degree),
            params[self.degree].sig_bound,
        )

    @property
    def poly_bytes(self):
        return math.ceil(self.degree * math.log2(self.q) / 8)

    def update(self, **kwargs) -> "Context":
        return Context(**(dto.asdict(self) | kwargs))

    @property
    def len_bits(self):
        return math.ceil(math.log2(self.q))

    @functools.cached_property
    def Zp(self):
        return Integers(self.q)

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
        return Zp(self.cbd(self.cbd_noise))

    def cbd(self, n: int):
        return random.binomialvariate(n, 0.5) - random.binomialvariate(n, 0.5)

    def random_element(self):
        return self.ZpxQ([self.Zp(randint(0, self.q - 1)) for _ in range(self.degree)])

    def random_vector(self):
        return vector(
            [self.random_element() for _ in range(self.k)], self.ZpxQ, immutable=True
        )

    @seeded_function
    def random_matrix(self):
        return matrix(
            [[self.random_element() for _ in range(self.k)] for _ in range(self.k)],
            base_ring=self.ZpxQ,
            immutable=True,
        )

    # FIX: Unneeded. Should be cleaned.
    def random_element_small(
        self,
        rand_function: typing.Callable[[], int] | None = None,
    ):
        if rand_function is None:
            rand_function = self.rand_function
        return self.ZpxQ([rand_function() for _ in range(self.degree)])

    def random_vector_small(
        self,
        size: int | None = None,
        like: PolyVec | None = None,
        rand_element: typing.Callable[[], int] | None = None,
    ):
        if size is None:
            size = self.k
        if like != None:
            size = len(like)
        if rand_element is None:
            rand_element = lambda: self.random_element_small()
        return vector([rand_element() for _ in range(size)], self.ZpxQ, immutable=True)

    _gauss_state: dict[int, typing.Callable[[], Poly]] = dto.field(default_factory=dict)
    def get_gauss(self, n: int) -> Poly:
        # NOTE: I cannot use lru_cache because ZpxQ is not hashable.
        if n not in self._gauss_state:
            self._gauss_state[n] = DisGauss(self.ZpxQ, self.degree, sigma=sqrt(n / 2))
        return self._gauss_state[n]()

    def r_small(self, n: int | None = None):
        """
        The purpose of this function is to change easily the
        type of random that the protocol uses.
        """
        if n is None:
            n = self.cbd_noise
        if n > 30:
            return self.get_gauss(n)
        return self.random_element_small(rand_function=lambda: self.cbd(n))

    def r_small_vector(self, n: int | None = None, like: PolyVec | None = None):
        size = self.k
        if n is None:
            n = self.k
        if like != None:
            size = len(like)
        return self.random_vector_small(
            size=size, rand_element=lambda: self.r_small(n)
        )

    def collapse_even_gen(self, v) -> typing.Generator[int, None, None]:
        p2 = self.q // 2
        m2 = (int(c) if int(c) <= p2 else int(c) - self.q for c in v)
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
        q2 = self.q // 2
        v1 = (int(coef) % self.q for coef in v)
        v2 = (coef if coef < q2 else self.q - coef for coef in v1)
        q4 = q2 // 2
        v3 = (0 if coef < q4 else 1 for coef in v2)
        return tuple(v3)

    def get_mask_of_element(self, v):
        p = self.q
        q2 = p // 2
        v1 = (int(coef) % p for coef in v)
        v2 = (coef if coef < q2 else p - coef for coef in v1)
        q4 = q2 // 2
        v3 = (abs(coef - q4) for coef in v2)
        v4 = ((c, i) for i, c in enumerate(v3))
        v5 = list(filter(lambda x: x[0] > self.safe_mask, v4))
        res = random.sample(v5, k=self.degree // 4)
        # gotta_go_fast breaks if not
        # but on normal executions it will still be 256
        res = [i for _, i in res]
        res = sorted(res)
        return res

    def apply_mask(self, ls, mask):
        return sum(x * 2**i for x, i in enumerate(ls[i] for i in mask))

    def from_ring(self, m: Poly) -> int:
        m_it = self.collapse(m)
        return sum(x << i for i, x in enumerate(m_it))

    def _gen_to_ring(self, m: int):
        q2 = self.q // 2
        for _ in range(self.degree):
            yield (m % 2) * q2
            m = m // 2

    def digest(self, a_seed: bytes, b: PolyVec) -> bytes:
        # NOTE: Hi ha molts molts bits del collapse
        b_bytes = b"".join(self.poly_to_bits(bi) for bi in b)
        return a_seed + b_bytes

    def from_digest(self, nyom: bytes) -> tuple[bytes, PolyVec]:
        a_seed = nyom[:32]
        b_digest: bytes = nyom[32:]
        b = self.bits_to_vector(b_digest)
        return a_seed, b

    def bits_to_vector(self, bits: bytes) -> PolyVec:
        res = []
        for start, end in it.pairwise(range(0, len(bits) + 1, self.poly_bytes)):
            res.append(self.bits_to_poly(bits[start:end]))
        return vector(res, self.ZpxQ, immutable=True)

    def bits_to_poly(self, bits: bytes) -> Poly:
        assert len(bits) == self.poly_bytes
        n = int.from_bytes(bits)
        res = []
        for _ in range(self.degree):
            res.append(n % self.q)
            n //= self.q
        if n != 0:
            print(f"bits_to_poly: n was not 0 {n}")
        res.reverse()
        return self.ZpxQ(res)

    def poly_to_bits(self, poly: Poly) -> bytes:
        def f(a: int, b: int) -> int:
            return a * self.q + b

        all_coefficients = map(int, poly)
        poly_int = fun.reduce(f, all_coefficients, 0)
        return poly_int.to_bytes(length=self.poly_bytes)

    def to_ring(self, m: int) -> Poly:
        return self.ZpxQ(list(self._gen_to_ring(m)))

    def inf_norm(self, zs: PolyVec):
        coefficients = it.chain.from_iterable(self.collapse_even_gen(z) for z in zs)
        return max(abs(x) for x in coefficients)


    def _to_array(self, vs: PolyVec):
        return np.array(
            list(it.chain.from_iterable(self.collapse_even(v) for v in vs)),
            dtype=np.int32,
        )

    def norm(self, z: PolyVec):
        return np.linalg.norm(self._to_array(z))
