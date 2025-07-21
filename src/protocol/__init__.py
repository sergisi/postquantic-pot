import dataclasses as dto
import secrets
from Crypto.Hash import SHAKE256
from Crypto.Cipher import AES

from src import ecoin, assymetric, ajtai
from src.context import get_context, gotta_go_fast_context
from src.context.context import AssymetricExtra, Context
from src.poly import PolyVec


type ProtocolContext = list[TransactionContext]


@dto.dataclass
class TransactionContext:
    """
    Contains all the necessities to perform the protocol.

    i.e. the set up.
    """

    fatctx: ecoin.ECoinCtx
    blindpk: assymetric.BlindPK


# TODO: Separar el set up del items preparation i que continui funcionant
def set_up_ecoins(
    max_coins: int = 16, degree: int = 1024
) -> tuple[Context[AssymetricExtra], list[ecoin.ECoinCtx]]:
    # NOTE: set-up
    ctx = get_context(degree)
    ecoins = [ecoin.get_ecoin_ctx(degree) for _ in range(max_coins)]
    return ctx, ecoins


def items_preparation(
    ctx: Context[AssymetricExtra], ecoins: list[ecoin.ECoinCtx]
) -> ProtocolContext:
    A = ctx.random_vector()
    C = ctx.random_vector()
    blindpks = [assymetric.create_merchant(fatctx.ctx, A, C) for fatctx in ecoins]
    return [
        TransactionContext(fatctx, blindpk) for fatctx, blindpk in zip(ecoins, blindpks)
    ]


def set_up_fast_pctx() -> ProtocolContext:
    max_coins = 4
    ctx = gotta_go_fast_context()
    ecoins = [ecoin.gotta_go_ecoin() for _ in range(max_coins)]
    A = ctx.random_vector()
    C = ctx.random_vector()
    blindpks = [assymetric.create_merchant(fatctx.ctx, A, C) for fatctx in ecoins]
    return [
        TransactionContext(fatctx, blindpk) for fatctx, blindpk in zip(ecoins, blindpks)
    ]


@dto.dataclass
class CachedEcoin:
    ecoin: ecoin.Ecoin
    s: PolyVec
    nizk: ajtai.AjtaiCommitment


type Wallet = list[CachedEcoin]


def create_coins(price: int, pctx: ProtocolContext) -> Wallet:
    wallet = []
    for i, trans in enumerate(pctx):
        if price & (1 << i) == 0:
            eco = ecoin.create_nonvalued(trans.fatctx)
        else:
            eco = ecoin.create_valued(trans.fatctx)
        s = trans.fatctx.ctx.r_small_vector()  # Default
        nizk = assymetric.blind_nizk(trans.blindpk, s)
        wallet.append(CachedEcoin(eco, s, nizk))
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
    for i, trans in enumerate(pctx):

        cpt = merchant_spend_coin(wallet[i].ecoin, wallet[i].nizk, trans.blindpk)
        # NOTE: This is executed by the Merchant for r1 and r2
        if price & (1 << i) != 0:
            valued_ecoin = wallet[i].ecoin
            assert isinstance(valued_ecoin, ecoin.Valued)
            key = valued_ecoin.kyb.dec(cpt.msg)
            cipher = AES.new(key.to_bytes(32), AES.MODE_EAX, nonce=cpt.nonce)
            byt = cipher.decrypt(cpt.ciphertext)
            cipher.verify(cpt.tag)
            r1, _ = trans.fatctx.ctx.bits_to_poly(byt)
            ab_product = r1 - trans.blindpk.r2 * wallet[i].s
            ctx = trans.fatctx.ctx
            blob = ctx.apply_mask(ctx.collapse(ab_product), trans.blindpk.mask)
            # assert blob == trans.blindpk.expected, f'Blob is not the same as expected:\n{blob}\n!=\n{trans.blindpk.expected}'
            key_gen.update(blob)
    return key_gen.read(32)
