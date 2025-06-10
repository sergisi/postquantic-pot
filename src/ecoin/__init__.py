import functools as fun
from random import randint
import secrets
import operator
import dataclasses as dto
from src.context import (
    DilithiumExtra,
    Context,
    get_dilithium_context,
    get_kyber_context,
    get_context,
    gotta_go_fast_context,
)
from src import ajtai, falcon
from src.context.context import AssymetricExtra
from src.poly import Poly, PolyVec
from . import kyber, dilithium, oaep


@dto.dataclass
class ECoinCtx:
    kyber: Context[None]
    dilithium: Context[DilithiumExtra]
    ctx: Context[AssymetricExtra]
    falcon: falcon.MyFalcon
    B1: PolyVec
    B2: PolyVec


def gotta_go_ecoin() -> ECoinCtx:
    ctx = gotta_go_fast_context()
    return ECoinCtx(
        kyber=get_kyber_context(),
        dilithium=get_dilithium_context(),
        ctx=ctx,
        falcon=falcon.MyFalcon(ctx),
        B1=ctx.random_vector(),
        B2=ctx.random_vector(),
    )


def get_ecoin_ctx(degree: int = 1024) -> ECoinCtx:
    ctx = get_context(degree)
    return ECoinCtx(
        kyber=get_kyber_context(),
        dilithium=get_dilithium_context(),
        ctx=ctx,
        falcon=falcon.MyFalcon(ctx),
        B1=ctx.random_vector(),
        B2=ctx.random_vector(),
    )


@dto.dataclass
class Valued:
    kyb: kyber.Kyber
    dil: dilithium.Dilithium
    r: bytes
    nizk: ajtai.AjtaiCommitment
    fatctx: ECoinCtx

    @property
    def blob(self):
        return bytes(map(operator.xor, self.kyb.digest()[1], self.dil.digest()[1]))

    @fun.cached_property
    def signature(self):
        return self.dil.sign(self.blob)

    @fun.cached_property
    def hy(self):
        """
        Hash of Y digest
        """
        _, y = oaep.enc(self.blob, self.r)
        return self.fatctx.ctx.bits_to_poly(y)[0]


@dto.dataclass
class NonValued:
    kyb: kyber.KyberPK
    dil: dilithium.Dilithium
    r: bytes
    nizk: ajtai.AjtaiCommitment
    fatctx: ECoinCtx

    @property
    def blob(self):
        return bytes(map(operator.xor, self.kyb.digest()[1], self.dil.digest()[1]))

    @fun.cached_property
    def signature(self):
        return self.dil.sign(self.blob)

    @fun.cached_property
    def hy(self) -> tuple[Poly, int]:
        """
        Hash of Y digest
        """
        _, y = oaep.enc(self.blob, self.r)
        return self.fatctx.ctx.bits_to_poly(y)[0]


type Ecoin = Valued | NonValued


def sum_all(matrices, vectors):
    return sum(A * y for A, y in zip(matrices, vectors))


def create_valued(fatctx: ECoinCtx):
    kyb = kyber.kyber_key_gen(fatctx.kyber)
    dil = dilithium.dilithium_key_gen(fatctx.dilithium)
    blob = bytes(map(operator.xor, kyb.digest()[1], dil.digest()[1]))
    r = secrets.token_bytes(fatctx.ctx.poly_bytes)
    x, y = oaep.enc(blob, r)
    hy, _ = fatctx.ctx.bits_to_poly(y)
    x = fatctx.ctx.r_small_vector()
    t = hy + fatctx.B1 * x
    s, r2 = merchant_blind_sign(t, fatctx)
    nizk = ajtai.ajtai_commitment(
        matrices=[fatctx.falcon.A, fatctx.B1, fatctx.B2],
        vectors=[s, -x, -r2],
        ctx=fatctx.ctx,
        f=sum_all,
    )
    return Valued(kyb, dil, r, nizk, fatctx)


def merchant_blind_sign(t: Poly, fatctx: ECoinCtx) -> tuple[PolyVec, PolyVec]:
    r2 = fatctx.ctx.r_small_vector()
    s = fatctx.falcon.my_sign(t + fatctx.B2 * r2)
    return s, r2


def create_nonvalued(fatctx: ECoinCtx) -> NonValued:
    s = fatctx.ctx.r_small_vector()
    x1 = fatctx.ctx.r_small_vector()
    r2 = fatctx.ctx.r_small_vector()
    # fatctx.ctx.

    hy = fatctx.falcon.A * s -  fatctx.B1 * x1 - fatctx.B2 * r2
    x = secrets.token_bytes(32)
    trash = randint(0, fatctx.ctx.max_trash)
    y = fatctx.ctx.poly_to_bits(hy, trash)
    blob, main_r = oaep.dec(x, y)
    dil = dilithium.dilithium_key_gen(fatctx.dilithium)
    x_s, y_s = dil.digest()
    y_r = bytes(map(operator.xor, blob, y_s))
    x_r = secrets.token_bytes(32 + fatctx.kyber.poly_bytes * fatctx.kyber.k)
    pk, r_r = oaep.dec(x_r, y_r)
    a_seed, b, trashbin = fatctx.kyber.from_digest(pk)
    kyb_pk = kyber.KyberPK(
        a_seed, fatctx.kyber.random_matrix(seed=a_seed), b, r_r, trashbin, fatctx.kyber
    )
    nizk = ajtai.ajtai_commitment(
        matrices=[fatctx.falcon.A, fatctx.B1, fatctx.B2],
        vectors=[s, -x1, -r2],
        ctx=fatctx.ctx,
        f=sum_all,
    )
    return NonValued(kyb_pk, dil, main_r, nizk, fatctx)


def merchant_spend(m: bytes, ecoin: Valued | NonValued):
    assert ecoin.nizk(), "Blind signature is correct"
    assert ecoin.nizk.t == ecoin.hy, f"{ecoin.nizk.t}\n !=\n {ecoin.hy}"
    assert ecoin.dil.verify(ecoin.blob, ecoin.signature), "It is signed"
    # FIX: Add ecoin has been spent.
    return ecoin.kyb.enc(int.from_bytes(m))
