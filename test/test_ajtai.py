import unittest

from sage.all import vector

from src.ajtai import ajtai_commitment
from src.context import Context, gotta_go_fast_context

from src.falcon import MyFalcon


def sum_all(matrices, vectors):
    return sum(A * y for A, y in zip(matrices, vectors))


class AjtaiTest(unittest.TestCase):
    ctx: Context

    def setUp(self) -> None:
        self.ctx = gotta_go_fast_context()
        return super().setUp()

    def test_ajtai(self):
        matrices = [self.ctx.random_vector() for _ in range(2)]
        vectors = [self.ctx.r_small_vector() for _ in range(2)]
        commitment = ajtai_commitment(matrices, vectors, self.ctx, sum_all)
        self.assertTrue(commitment())

    def test_ajtai_3vectors(self):
        matrices = [self.ctx.random_vector() for _ in range(3)]
        vectors = [self.ctx.r_small_vector() for _ in range(3)]
        commitment = ajtai_commitment(matrices, vectors, self.ctx, sum_all)
        self.assertTrue(commitment())

    def test_ajtai_one_as_falcon_matrix(self):
        """Ajtai Commitment seems to break when actually used in the
        protocol. No clue why"""
        matrices = [self.ctx.random_vector() for _ in range(3)]
        matrices[0] = vector([1, self.ctx.random_element()], self.ctx.ZpxQ)
        vectors = [-self.ctx.r_small_vector() for _ in range(3)]
        vectors[0] = -vectors[0]
        commitment = ajtai_commitment(matrices, vectors, self.ctx, sum_all)
        self.assertTrue(commitment())

    def test_what(self):
        falc = MyFalcon(self.ctx)
        matrices = [self.ctx.random_vector() for _ in range(3)]
        matrices[0] = falc.A
        vectors = [-self.ctx.r_small_vector() for _ in range(3)]
        m = self.ctx.r_small()
        s = falc.my_sign(m)
        vectors[0] = s
        commitment = ajtai_commitment(matrices, vectors, self.ctx, sum_all)
        self.assertTrue(commitment())
