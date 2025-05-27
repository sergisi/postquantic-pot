import dataclasses as dto
import operator
import secrets
from Crypto.Hash import SHAKE256

from src import ecoin, assymetric, ajtai
from src.poly import PolyVec


@dto.dataclass
class ProtocolContext:
    """
    Contains all the necessities to perform the protocol.

    i.e. the set up.
    """

    fatctx: ecoin.FatContext
    blindpk: list[assymetric.BlindPK]
    """
    Represents the maximum number of coins. the values are 
    represented on binary, so the maximum price will be
    2 ** max_coins - 1
    """
    max_coins: int


def set_up_fast() -> ProtocolContext:
    max_coins = 16
    fatctx = ecoin.gotta_go_fat()
    blindpk = [assymetric.create_merchant(fatctx.ctx) for _ in range(max_coins)]
    return ProtocolContext(fatctx=fatctx, blindpk=blindpk, max_coins=max_coins)


type Wallet = list[ecoin.Ecoin]


def create_coins(price: int, pctx: ProtocolContext) -> Wallet:
    wallet = []
    for i in range(pctx.max_coins):
        if price & (1 << i) == 0:
            wallet.append(ecoin.create_nonvalued(pctx.fatctx))
        else:
            wallet.append(ecoin.create_valued(pctx.fatctx))
    return wallet


def merchant_spend_coin(
    eco: ecoin.Ecoin, nizk: ajtai.AjtaiCommitment, bpk: assymetric.BlindPK
) -> tuple[bytes, tuple[PolyVec, PolyVec]]:
    r1 = bpk.compute_r1(nizk)
    trash = secrets.randbelow(bpk.ctx.max_trash + 1)
    byt = bpk.ctx.poly_to_bits(r1, trash)
    key = secrets.token_bytes(32)
    xof = SHAKE256.new(key)
    enc_byt = bytes(map(operator.xor, byt, xof.read(len(byt))))
    msg = ecoin.merchant_spend(key, eco)
    return enc_byt, msg
