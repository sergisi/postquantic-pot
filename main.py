"""
Module for postquantic pot.


"""

# TODO: Add NIZK on the protocol.
import time
from concurrent.futures import ProcessPoolExecutor
import dataclasses as dto
import itertools
import functools
from src.context import Context, get_context
from src.poly import Poly, PolyVec
from src.count import *
from src import ajtai

@dto.dataclass
class Merchant:
    b: Poly
    a: PolyVec
    A: PolyVec
    C: PolyVec
    expected_message: PolyVec
    mask: list[int]
    e2: PolyVec
    r2: PolyVec

    ctx: Context

    @functools.cached_property
    def expected(self):
        return self.ctx.apply_mask(self.ctx.collapse(self.expected_message), self.mask)

    def compute_r1(self, nizk) -> Poly:
        assert nizk()
        c = nizk.t
        e1 = self.ctx.r_small(self.ctx.e1_param)
        return self.b * c + e1


def create_merchant(ctx: Context):
    # bob_count.n += n_elems + n_cols * 2 + n_matrix * 2
    b = ctx.random_element()
    a = ctx.r_small_vector()
    A = ctx.random_vector()
    C = ctx.random_vector()
    expected_message = b * A * a
    mask = ctx.get_mask_of_element(expected_message)
    # not counted
    e2 = ctx.r_small_vector(ctx.e2_param)
    r2 = b * C + e2
    return Merchant(b, a, A, C, expected_message, mask, e2, r2, ctx)


@dto.dataclass
class ProtocolData:
    s: PolyVec
    nizk: ajtai.AjtaiCommitment
    r1: Poly
    ab_product: Poly
    actual: PolyVec


@dto.dataclass
class CPlanData:
    set_up_data: Merchant
    protocol_data: ProtocolData

    def check(self):
        return self.set_up_data.expected == self.protocol_data.actual


def _nizk(merchant: Merchant, s, ctx: Context) -> ajtai.AjtaiCommitment:
        return ajtai.ajtai_commitment(
            [merchant.A, merchant.C], [merchant.a, s], ctx, 
        f=lambda xs, ys: xs[0] * ys[0] + xs[1] * ys[1]
        )


def _protocol(merchant: Merchant, ctx: Context) -> ProtocolData:
    s = ctx.r_small_vector()  # Default
    # TODO: Add ajtai here
    # NOTE: This is executed by Bob
    nizk = _nizk(merchant, s, ctx)
    r1 = merchant.compute_r1(nizk)
    ab_product = r1 - merchant.r2 * s
    actual = ctx.apply_mask(ctx.collapse(ab_product), merchant.mask)
    return ProtocolData(s, nizk, r1, ab_product, actual)


def protocol(cbd_noise=2, e1_param=100_000, e2_param=200):
    ctx = get_context(cbd_noise, e1_param, e2_param)
    set_up_data = create_merchant(ctx)
    protocol_data = _protocol(set_up_data, ctx)
    data = CPlanData(set_up_data, protocol_data)
    return data.check()


def protocol_collect_data(cbd_noise=2, e1_param=100_000, e2_param=200):
    ctx = get_context(cbd_noise, e1_param, e2_param)
    set_up_data = create_merchant(ctx)
    protocol_data = _protocol(set_up_data, ctx)
    data = CPlanData(set_up_data, protocol_data)
    return None if data.check() else data


def check_some(_):
    res = []
    for e in (protocol_collect_data() for _ in range(1000)):
        if e is not None:
            res.append(e)
    return res


def collect_data():
    with ProcessPoolExecutor(max_workers=8) as executor:
        ls = executor.map(check_some, range(8))
        return list(itertools.chain(*ls))


def _study_singular_time(_, cbd_noise=2, e1_param=100_000, e2_param=200):
    ctx = get_context(cbd_noise, e1_param, e2_param)
    t0 = time.time()
    set_up_data = create_merchant(ctx)
    t1 = time.time()
    _ = _protocol(set_up_data, ctx)
    t2 = time.time()
    return t1 - t0, t2 - t1


def study_time():
    with ProcessPoolExecutor() as executor:
        for t1, t2 in executor.map(_study_singular_time, range(10_000)):
            yield t1, t2


def write_study_time():
    with open("time.csv", "w") as f:
        for t1, t2 in study_time():
            print(f"{t1}, {t2}", file=f)


# Test that homomorphic is working.
# test_homomorphic()
# Test is not needed, less bits is also efficient.
assert protocol()  # messes with the count


import cProfile

if __name__ == "__main__":
    # cProfile.run('protocol()')
    print("\n\n\n\n\n\n\n")
