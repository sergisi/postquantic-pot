"""
Computes As = m

Without hashing to point.

Returns s as a RingElement in the context of
Falcon(ctx.degree), and only Falcon1024.

A is also shown as a Matrix when created.
"""

from .falcon import SecretKey
from ..context import Context
import functools as fun
from sage.all import vector


class MyFalcon(SecretKey):
    ctx: Context

    def __init__(self, ctx: Context):
        self.ctx = ctx
        super().__init__(n=ctx.degree)

    @fun.cached_property
    def A(self):
        return vector([1, self.h], self.ctx.ZpxQ)

    def to_falcon_point(self, message):
        return self.ctx.collapse_even(message)

    def to_sagemath_vector(self, s):
        return vector(s, self.ctx.ZpxQ)

    def my_sign(self, message):
        """
        Hack of sign. Message is RingElement from context and
        it's just transformed to 'hashed' by transforming
        the representation to the one used by falcon.py.
        """
        # int_header = 0x30 + logn[self.n]
        # header = int_header.to_bytes(1, "little")
        # salt = randombytes(SALT_LEN)
        # hashed = self.hash_to_point(message, salt)
        hashed = self.to_falcon_point(message)

        # We repeat the signing procedure until we find a signature that is
        # short enough (both the Euclidean norm and the bytelength)
        for _ in range(200):
            s = self.sample_preimage(hashed)
            norm_sign = sum(coef**2 for coef in s[0])
            norm_sign += sum(coef**2 for coef in s[1])
            # Check the Euclidean norm
            if norm_sign <= self.signature_bound:
                return self.to_sagemath_vector(s)
        raise Exception("Falcon failed to sign the message!")

    def my_verify(self, message, s):
        """
        Verify a signature.
        """
        norm_sign = sum(coef**2 for coef in self.ctx.collapse_even(s[0]))
        norm_sign += sum(coef**2 for coef in self.ctx.collapse_even(s[1]))
        h_poly = self.ctx.ZpxQ(self.h)
        s0 = s[0]
        s1 = s[1]
        return norm_sign <= self.signature_bound and message - h_poly * s1 == s0
