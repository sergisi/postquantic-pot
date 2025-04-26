import collections
import dataclasses as dto
import typing

from sage.all import PolynomialRing, matrix, vector
from src import falcon
from src.poly import Poly, PolyVec
from .pk import PublicKey, aes, AESCyphertext
from src.context import Context
from src.ajtai import AjtaiCommitment


@dto.dataclass
class Bank:
    """
    Represents the issuer in the protocol.
    """

    pk: PublicKey
    falcon: falcon.MyFalcon
    ctx: Context
    identity_db: dict[Poly, str] = dto.field(default_factory=dict)
    before_message: dict[PolyVec, list[tuple[PolyVec, Poly]]] = dto.field(
        default_factory=lambda: collections.defaultdict(list)
    )
    total: int = 0
    counter: int = 0

    def set_customer(
        self, id_pk: PolyVec, identity: str, nizk: AjtaiCommitment
    ) -> None:
        assert nizk()
        self.identity_db[id_pk] = identity

    def generate_ecoin(
        self, t: PolyVec, id_pk: Poly, identity: str, nizk: AjtaiCommitment
    ) -> tuple[PolyVec, PolyVec]:
        self.set_customer(id_pk, identity, nizk)
        r2 = self.ctx.r_small_vector()
        return self.falcon.my_sign(self.pk.b2_mat * r2 + t + id_pk), r2

    def gen_ej_mat(self):
        return self.ctx.random_vector(like=self.pk.d_mat)

    def _solve_equation(self, mat, res):
        """
        Solve the system of equations mat * y = res
        """
        return mat.inverse() * res

    def spend_ecoin(
        self,
        commitment: AjtaiCommitment,
        ej_mat: PolyVec,
        ej: Poly,
        m: PolyVec,
    ) -> str | bool | None:
        if not commitment():
            return False
        for ek_mat, ek in self.before_message[m]:
            mat = matrix(self.ctx.ZpxQ, [self.pk.d_mat, ek_mat, ej_mat])
            try:
                self.total += 1
                mat_inverse = mat.inverse()
            except:
                self.counter += 1
                return None
            for p in self.identity_db.keys():
                expected = vector(self.ctx.ZpxQ, [p, ek, ej])
                maybe_x = mat_inverse * expected
                norm = self.ctx.norm(maybe_x)
                has_double_spend = norm <= 200
                if has_double_spend:
                    return self.identity_db[p]
        self.before_message[m].append((ej_mat, ej))
        return True
