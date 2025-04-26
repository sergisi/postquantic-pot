import dataclasses as dto
from src.poly import PolyVec


@dto.dataclass
class PublicKey:
    a_mat: PolyVec
    b0_mat: PolyVec
    b1_mat: PolyVec
    b2_mat: PolyVec
    d_mat: PolyVec


@dto.dataclass
class AESCyphertext:
    b: PolyVec
    s: PolyVec
    key: int

    def decrypt(self, key: int):
        if key == self.key:
            return self.b, self.s
        raise Exception("Not decrypted correctly")


def aes(b, s, key: int) -> AESCyphertext:
    return AESCyphertext(b, s, key)
