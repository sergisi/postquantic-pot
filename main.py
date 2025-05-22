"""
Module for postquantic pot.


"""

import dataclasses as dto
import functools as fun
from src.context import Context, get_context, AssymetricExtra
from src.poly import Poly, PolyVec
from src.count import *
from src import ajtai

@dto.dataclass
class BlindPK:
    """
    BlindPK that merchant uses to create the assymetric 
    blind operation.

    """
    b: Poly
    a: PolyVec
    A: PolyVec
    C: PolyVec
    expected_message: PolyVec
    mask: list[int]
    e2: PolyVec
    r2: PolyVec
    ctx: Context[AssymetricExtra]

    @fun.cached_property
    def expected(self):
        return self.ctx.apply_mask(self.ctx.collapse(self.expected_message), self.mask)

    def compute_r1(self, nizk) -> Poly:
        assert nizk()
        c = nizk.t
        e1 = self.ctx.r_small(self.ctx.more.e1_param)
        return self.b * c + e1


def create_merchant(ctx: Context) -> BlindPK:
    # bob_count.n += n_elems + n_cols * 2 + n_matrix * 2
    b = ctx.random_element()
    a = ctx.r_small_vector()
    A = ctx.random_vector()
    C = ctx.random_vector()
    expected_message = b * A * a
    mask = ctx.get_mask_of_element(expected_message)
    # not counted
    e2 = ctx.r_small_vector(ctx.more.e2_param)
    r2 = b * C + e2
    return BlindPK(b, a, A, C, expected_message, mask, e2, r2, ctx)


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


if __name__ == "__main__":
    assert protocol()  # messes with the count


