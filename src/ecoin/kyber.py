import random
import secrets
from . import oaep
from src.context import Context
from src.poly import PolyVec, PolyMat
import functools as fun
import dataclasses as dto


@dto.dataclass
class KyberPK:
    a_seed: bytes

    A: PolyMat
    b: PolyVec
    r: bytes
    trashbin: bytes
    ctx: Context[None]



    def digest(self) -> tuple[bytes, bytes]:
        """
        32 bytes that represents the dilithium pk.

        """
        message = self.ctx.digest(self.a_seed, self.b, self.trashbin)
        return oaep.enc(message, self.r)

    def enc(self, m: int) -> tuple[PolyVec, PolyVec]:
        r = self.ctx.r_small_vector()
        e1 = self.ctx.r_small_vector()
        e2 = self.ctx.r_small()
        return (self.A.transpose() * r + e1, self.b * r + e2 + self.ctx.to_ring(m))


@dto.dataclass()
class Kyber:
    a_seed: bytes

    A: PolyMat
    s: PolyVec
    e: PolyVec
    ctx: Context[None]

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

    @fun.cached_property
    def b(self):
        return self.A * self.s + self.e

    def enc(self, m: int) -> tuple[PolyVec, PolyVec]:
        r = self.ctx.r_small_vector()
        e1 = self.ctx.r_small_vector()
        e2 = self.ctx.r_small()
        return (self.A.transpose() * r + e1, 
                self.b * r + e2 + self.ctx.to_ring(m))

    def dec(self, c):
        u, v = c
        return self.ctx.from_ring(v - self.s * u)


def kyber_key_gen(ctx: Context[None]) -> Kyber:
    a_seed: bytes = random.randbytes(32)
    A = ctx.random_matrix(seed=a_seed)
    return Kyber(a_seed, A, ctx.r_small_vector(), ctx.r_small_vector(), ctx)
