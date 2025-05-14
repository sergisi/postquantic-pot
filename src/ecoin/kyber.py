import random
from src.context.kyber_context import KyberContext
from src.poly import Poly, PolyVec, PolyMat
import functools as fun
import dataclasses as dto


@dto.dataclass()
class Kyber:
    a_seed: bytes

    A: PolyMat
    s: PolyVec
    e: PolyVec
    ctx: KyberContext

    @fun.cached_property
    def b(self):
        return self.A * self.s + self.e

    def enc(self, m: int):
        r = self.ctx.r_small_vector()
        e1 = self.ctx.r_small_vector()
        e2 = self.ctx.r_small()
        return (self.A.transpose() * r + e1, self.b * r + e2 + self.ctx.to_ring(m))

    def dec(self, c):
        u, v = c
        return self.ctx.from_ring(v - self.s * u)


def kyber_key_gen(ctx: KyberContext) -> Kyber:
    a_seed: bytes = random.randbytes(32)
    A = ctx.random_matrix(seed=int.from_bytes(a_seed))
    return Kyber(a_seed, A, ctx.r_small_vector(), ctx.r_small_vector(), ctx)
