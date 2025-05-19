import typing
import operator
import dataclasses as dto

from src.context import Context
from src.context import DilithiumExtra, Context, get_kyber_context
from . import kyber
from . import dilithium


@dto.dataclass
class Valued:
    kyber: kyber.Kyber
    dilithium: dilithium.Dilithium
    signed_message: bytes



@dto.dataclass
class NonValued:
    pass

type MerchantSigns = typing.Any


class FatContext:
    kyber: Context[None]
    dilithium: Context[DilithiumExtra]
    falcon: Context

def create_valued(merchant: MerchantSigns, fatctx: FatContext) -> Valued:
    pk_kyber = kyber.kyber_key_gen(fatctx.kyber)
    pk_dilithium = dilithium.dilithium_key_gen(fatctx.dilithium)
    blob = bytes(map(operator.xor, pk_kyber.digest() , pk_dilithium.digest()))

    signature = merchant.blind_sign(blob)
    return Valued(pk_kyber, pk_dilithium, signature)
    
