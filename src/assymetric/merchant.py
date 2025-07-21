"""
Module for postquantic pot.


"""

import dataclasses as dto
import functools as fun
from src.context import Context, AssymetricExtra
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
    # NOTE: this is for testing. Please remove in a serious implementation
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


# , A: PolyVec, C: PolyVec
def create_merchant(ctx: Context[AssymetricExtra], A: PolyVec, C: PolyVec) -> BlindPK:
    # bob_count.n += n_elems + n_cols * 2 + n_matrix * 2
    b = ctx.random_element()
    a = ctx.r_small_vector()
    expected_message = b * A * a
    # NOTE: This should be made for each item in
    mask = ctx.get_mask_of_element(expected_message)
    # not counted
    e2 = ctx.r_small_vector(ctx.more.e2_param)
    r2 = b * C + e2
    return BlindPK(b, a, A, C, expected_message, mask, e2, r2, ctx)
