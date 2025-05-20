import random
import typing
import operator
import dataclasses as dto

from src.context import Context, get_dilithium_context
from src.context import DilithiumExtra, Context, get_kyber_context
from src import ajtai, falcon
from src.context.context import AssymetricExtra
from src.poly import Poly, PolyVec
from . import kyber, dilithium, oaep


@dto.dataclass
class Valued:
    kyber: kyber.Kyber
    dilithium: dilithium.Dilithium
    r: bytes
    nizk: ajtai.AjtaiCommitment



@dto.dataclass
class NonValued:
    kyber: kyber.KyberPK
    dilithium: dilithium.Dilithium
    r: bytes 
    nizk: ajtai.AjtaiCommitment


class FatContext:
    kyber: Context[None]
    dilithium: Context[DilithiumExtra]
    ctx: Context[AssymetricExtra]
    falcon: falcon.MyFalcon
    B: PolyVec


def sum_all(matrices, vectors):
    return sum(A * y for A, y in zip(matrices, vectors))


def customer_generate_ecoin(fatctx: FatContext):
    kyb = kyber.kyber_key_gen(fatctx.kyber)
    dil = dilithium.dilithium_key_gen(fatctx.dilithium)
    blob = bytes(map(operator.xor, kyb.digest() , dil.digest()))
    r = random.randbytes(fatctx.ctx.poly_bytes * fatctx.ctx.k)
    x, y = oaep.enc(blob, r)
    hy = fatctx.ctx.bits_to_vector(y)
    x = fatctx.ctx.r_small_vector()
    t = hy - fatctx.falcon.A * x
    s, r2 = merchant_blind_sign(t, fatctx)
    s_prime = s + x
    nizk = ajtai.ajtai_commitment(
        matrices=[fatctx.falcon.A, fatctx.B],
        vectors=[s_prime, -r2],
        ctx=fatctx.ctx,
        f=sum_all
    )
    return Valued(kyb, dil, r, nizk)



def merchant_blind_sign(t: Poly, fatctx: FatContext) -> tuple[PolyVec, PolyVec]:
    r2 = fatctx.ctx.r_small_vector()
    s = fatctx.falcon.my_sign(t + fatctx.B * r2)
    return s, r2

def generate_nonvalued(fatctx: FatContext) -> NonValued:
    s_prime = fatctx.ctx.r_small_vector()
    r2 = fatctx.ctx.r_small_vector()
    hy = fatctx.falcon.A * s_prime - fatctx.B * r2
    x = random.randbytes(32)
    blob, r = oaep.dec(hy, x)
    dil = dilithium.dilithium_key_gen(fatctx.dilithium)
    _, y_s = dil.digest()
    y_r = bytes(map(operator.xor, blob, y_s))
    x_r = random.randbytes(32 + fatctx.kyber.poly_bytes * fatctx.kyber.k)
    pk, r_r = oaep.dec(x_r, y_r)
    a_seed, b = fatctx.kyber.from_digest(pk)
    kyb_pk = kyber.KyberPK(a_seed, fatctx.kyber.random_matrix(seed=a_seed), b, r_r, fatctx.kyber)
    nizk = ajtai.ajtai_commitment(
        matrices=[fatctx.falcon.A, fatctx.B],
        vectors=[s_prime, -r2],
        ctx=fatctx.ctx,
        f=sum_all
    )
    return NonValued(kyb_pk, dil, r, nizk)



