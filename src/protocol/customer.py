import dataclasses as dto
import operator
import functools as fun
import collections
import itertools

from src.poly import Poly, PolyVec
from .pk import PublicKey
from src.context import Context
from src import ajtai
from .data_structures import Ecoin
from .bank import Bank


@dto.dataclass
class Customer:
    """
    Represents the customer
    """

    pk: PublicKey
    ctx: Context
    identity: str

    def gen_id_x(self) -> PolyVec:
        return self.ctx.r_small_vector(like=self.pk.d_mat)

    def id_pk(self, id_x) -> Poly:
        return self.pk.d_mat * id_x

    def nizk(self, id_x) -> ajtai.AjtaiCommitment:
        return ajtai.ajtai_commitment(
            [self.pk.d_mat], [id_x], self.ctx, f=lambda xs, ys: xs[0] * ys[0]
        )

    def generate_ecoin(self, bank: Bank) -> Ecoin:
        m = self.ctx.r_small_vector()
        r1 = self.ctx.r_small_vector()
        t = self.pk.b0_mat * m + self.pk.b1_mat * r1
        id_x = self.gen_id_x()
        nizk = self.nizk(id_x)
        # NOTE: Needs ajtai?
        s, r2 = bank.generate_ecoin(t, self.id_pk(id_x), self.identity, nizk)
        return Ecoin(m, r1, r2, s, id_x)

    def spend_ecoin(self, bank: Bank, ecoin: Ecoin) -> str | bool | None:
        res = None
        for _ in range(200):
            ej_mat = bank.gen_ej_mat()
            matrices = [
                self.pk.d_mat,
                self.pk.b1_mat,
                self.pk.b2_mat,
                self.pk.a_mat,
                ej_mat,
            ]
            vectors = [ecoin.id_x, ecoin.r1, ecoin.r2, ecoin.s]
            commitment = ajtai.ajtai_commitment(
                matrices,
                vectors,
                self.ctx,
                ajtai_commitment_function,
                prior_to_hash=itertools.chain.from_iterable,
            )
            assert commitment.t[0] == -self.pk.b0_mat * ecoin.m, self.identity
            assert commitment()
            res = bank.spend_ecoin(commitment, ej_mat, ej_mat * ecoin.id_x, ecoin.m)
            if res != None:
                return res
        raise Exception("Could not spend the e-coin.")


def ajtai_commitment_function(
    matrices: list[PolyVec], vectors: list[PolyVec]
) -> list[PolyVec]:
    d_mat, b1_mat, b2_mat, a_mat, ej_mat = matrices
    x, r1, r2, s = vectors
    return [d_mat * x + b1_mat * r1 + b2_mat * r2 - a_mat * s, ej_mat * x]
