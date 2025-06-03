import dataclasses as dto
import secrets
from Crypto.Hash import SHAKE256
from Crypto.Cipher import AES

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
    max_coins: int
    """
    Represents the maximum number of coins. the values are 
    represented on binary, so the maximum price will be
    $2 ^ {max_coins} - 1$
    """


def set_up_pctx(max_coins: int=16, degree: int=1024) -> ProtocolContext:
    fatctx = ecoin.get_fatctx(degree)
    blindpk = [assymetric.create_merchant(fatctx.ctx) for _ in range(max_coins)]
    return ProtocolContext(fatctx=fatctx, blindpk=blindpk, max_coins=max_coins)

def set_up_fast_pctx() -> ProtocolContext:
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


@dto.dataclass
class CoinCiphertext:
    ciphertext: bytes
    tag: bytes
    nonce: bytes
    msg: tuple[PolyVec, PolyVec]

def merchant_spend_coin(
    eco: ecoin.Ecoin, nizk: ajtai.AjtaiCommitment, bpk: assymetric.BlindPK
) -> CoinCiphertext:
    r1 = bpk.compute_r1(nizk)
    trash = secrets.randbelow(bpk.ctx.max_trash + 1)
    byt = bpk.ctx.poly_to_bits(r1, trash)
    key = secrets.token_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(byt)
    msg = ecoin.merchant_spend(key, eco)
    return CoinCiphertext(ciphertext, tag, cipher.nonce, msg)

def customer_spend_coin(price: int, wallet: Wallet, pctx: ProtocolContext) -> bytes:
    key_gen = SHAKE256.new()
    for i in range(pctx.max_coins):
        s = pctx.fatctx.ctx.r_small_vector()  # Default
        nizk = assymetric.blind_nizk(pctx.blindpk[i], s, pctx.fatctx.ctx)
        # NOTE: This is executed by the Merchant for r1 and r2
        cpt = merchant_spend_coin(wallet[i], nizk, pctx.blindpk[i])
        if price & (1 << i) != 0:
            valued_ecoin= wallet[i]
            assert isinstance(valued_ecoin, ecoin.Valued)
            key = valued_ecoin.kyb.dec(cpt.msg)
            cipher = AES.new(key.to_bytes(32), AES.MODE_EAX, nonce=cpt.nonce)
            byt = cipher.decrypt(cpt.ciphertext)
            cipher.verify(cpt.tag)
            r1, _ = pctx.fatctx.ctx.bits_to_poly(byt)
            ab_product = r1 - pctx.blindpk[i].r2 * s
            ctx = pctx.fatctx.ctx
            blob = ctx.apply_mask(ctx.collapse(ab_product), pctx.blindpk[i].mask)
            key_gen.update(blob)
    return key_gen.read(32)

