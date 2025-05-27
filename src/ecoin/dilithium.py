import random
from . import oaep
import secrets
import dataclasses as dto
from Crypto.Hash import SHAKE256
import functools as fun
import itertools as it
from src.context import Context, DilithiumExtra
from src.poly import Poly, PolyMat, PolyVec


def _centered_mod(i: int, alpha: int):
    j = i % alpha
    alpha2 = alpha // 2
    if j >= alpha2:
        return j - alpha
    return j


def _convert_poly(alpha: int):
    def f(zi: Poly):
        return [_centered_mod(int(zc), alpha) for zc in zi]

    return f


def centered_mod(z: PolyVec, alpha: int):
    return z.map_coefficients(_convert_poly(alpha))


def f(a: int, b: int) -> int:
    return a * 64 + b


def collapse_bits(z: PolyVec) -> int:
    all_coefficients = list(map(int, it.chain.from_iterable(z)))
    return fun.reduce(f, all_coefficients, 0)


@dto.dataclass
class Dilithium:
    a_seed: bytes
    A: PolyMat
    s: PolyVec
    b: PolyVec
    ctx: Context[DilithiumExtra]

    @fun.cached_property
    def r(self):
        """
        r to convert the pk. Cached so that is replicable.

        """
        return secrets.token_bytes(32)

    @fun.cached_property
    def trashbin(self):
        """
        trashbin to convert the pk. Cached so that is replicable.

        """
        return self.ctx.gen_trashbin()

    def digest(self) -> tuple[bytes, bytes]:
        """
        32 bytes that represents the dilithium pk.

        """
        message = self.ctx.digest(self.a_seed, self.b, self.trashbin)
        return oaep.enc(message, self.r)

    def rej_sampling(self, z: PolyVec, y: PolyVec, c: Poly) -> bool:
        return (
            self.ctx.inf_norm(z) < self.ctx.more.gamma1 - self.ctx.more.beta
            and self.ctx.inf_norm(
                self.low_bits(self.A * y - c * self.s, self.double_gamma2)
            )
            < self.ctx.more.gamma2 - self.ctx.more.beta
        )

    def decompose(self, r: PolyVec, alpha: int) -> tuple[int, int]:
        r0 = centered_mod(r, alpha)
        if r - r0 == self.ctx.q - 1:
            return r0 - 1, 0
        r1 = (r - r0).map_coefficients(lambda zi: [zc // alpha for zc in zi])
        return r0, r1

    def low_bits(self, z: PolyVec, alpha: int) -> int:
        return self.decompose(z, alpha)[0]

    def high_bits(self, z: PolyVec, alpha: int) -> int:
        element = self.decompose(z, alpha)[1]
        return collapse_bits(element)

    def _to_bytes(self, i: int | bytes) -> bytes:
        if isinstance(i, bytes):
            return i
        return i.to_bytes(i.bit_length())

    def hash_to_point(self, message: int | bytes, salt: int | bytes) -> Poly:
        xof = SHAKE256.new()
        xof.update(self._to_bytes(message))
        xof.update(self._to_bytes(salt))

        def get_i(i):
            while True:
                j = xof.read(1)[0]
                if j <= i:
                    return j

        sign_bytes = xof.read(8)
        sign_int = int.from_bytes(sign_bytes, "little")
        coeffs = [0 for _ in range(self.ctx.degree)]
        for i in range(256 - self.ctx.more.tau, 256):
            j = get_i(i)
            coeffs[i] = coeffs[j]
            coeffs[j] = 1 - 2 * (sign_int & 1)
            sign_int >>= 1
        return self.ctx.ZpxQ(coeffs)

    @property
    def double_gamma2(self):
        return 2 * self.ctx.more.gamma2

    def sign(self, m: int | bytes) -> tuple[PolyVec, Poly]:
        # NOTE: Figure 1 algorithm on \cite{dilithium-spec}
        for _ in range(20):
            y = self.ctx.r_small_vector(self.ctx.l)
            w = self.high_bits(self.A * y, self.double_gamma2)
            c = self.hash_to_point(m, w)
            z = y + c * self.s
            if self.rej_sampling(z, y, c):
                return z, c
        raise Exception("Could not generate the signature")

    def verify(self, m, sig) -> bool:
        z, c = sig
        w = self.high_bits(self.A * z - c * self.b, self.double_gamma2)
        return self.ctx.inf_norm(
            z
        ) < self.ctx.more.gamma1 - self.ctx.more.beta and c == self.hash_to_point(m, w)


def dilithium_key_gen(ctx: Context[DilithiumExtra]) -> Dilithium:
    a_seed: bytes = random.randbytes(32)
    A = ctx.random_matrix(seed=a_seed)
    s = ctx.r_small_vector(ctx.l)
    e = ctx.r_small_vector(ctx.k)
    b = A * s + e
    return Dilithium(a_seed, A, s, b, ctx)
