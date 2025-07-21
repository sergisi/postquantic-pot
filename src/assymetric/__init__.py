from src import ajtai
from src.context import Context, get_context
from src.poly import PolyVec
from .merchant import BlindPK, create_merchant


def blind_nizk(merchant: BlindPK, s: PolyVec) -> ajtai.AjtaiCommitment:
    return ajtai.ajtai_commitment(
        [merchant.A, merchant.C],
        [merchant.a, s],
        merchant.ctx,
        f=lambda xs, ys: xs[0] * ys[0] + xs[1] * ys[1],
    )


def _protocol(merchant: BlindPK, ctx: Context) -> bytes:
    s = ctx.r_small_vector()  # Default
    nizk = blind_nizk(merchant, s)
    # NOTE: This is executed by the Merchant for r1 and r2
    r1 = merchant.compute_r1(nizk)
    ab_product = r1 - merchant.r2 * s
    return ctx.apply_mask(ctx.collapse(ab_product), merchant.mask)


def protocol(cbd_noise=2, e1_param=39967, e2_param=2) -> bool:
    ctx = get_context(cbd_noise, e1_param, e2_param)
    set_up_data = create_merchant(ctx)
    key_got = _protocol(set_up_data, ctx)
    breakpoint()
    return set_up_data.expected_message == key_got
