from src import ajtai
from src.context import Context
from src.poly import PolyVec
from .merchant import BlindPK, get_context, create_merchant


def _nizk(merchant: BlindPK, s: PolyVec, ctx: Context) -> ajtai.AjtaiCommitment:
        return ajtai.ajtai_commitment(
            [merchant.A, merchant.C], [merchant.a, s], ctx, 
        f=lambda xs, ys: xs[0] * ys[0] + xs[1] * ys[1]
        )


def _protocol(merchant: BlindPK, ctx: Context) -> int:
    s = ctx.r_small_vector()  # Default
    nizk = _nizk(merchant, s, ctx)
    # NOTE: This is executed by the Merchant for r1 and r2
    r1 = merchant.compute_r1(nizk)
    ab_product = r1 - merchant.r2 * s
    return ctx.apply_mask(ctx.collapse(ab_product), merchant.mask)


def protocol(cbd_noise=2, e1_param=100_000, e2_param=200):
    ctx = get_context(cbd_noise, e1_param, e2_param)
    set_up_data = create_merchant(ctx)
    key_got = _protocol(set_up_data, ctx)
    return set_up_data.expected_message == key_got


