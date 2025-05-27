import unittest
from src.ecoin.kyber import kyber_key_gen, Kyber
from src.context import get_kyber_context, Context
from src.poly import Poly, PolyVec, PolyMat
import functools as fun
import dataclasses as dto
import random


class TestKyber(unittest.TestCase):
    ctx: Context[None]
    kyber: Kyber

    def setUp(self):
        self.ctx = get_kyber_context()
        self.kyber = kyber_key_gen(self.ctx)
        super().setUp()

    def test_isomorphic(self):
        message = random.getrandbits(256)
        enc_m = self.kyber.enc(message)
        dec_m = self.kyber.dec(enc_m)
        self.assertEqual(message, dec_m)

    def test_digest_and_from(self):
        digest = self.ctx.digest(self.kyber.a_seed, self.kyber.b, self.kyber.trashbin)
        digest2 = self.ctx.digest(self.kyber.a_seed, self.kyber.b, self.kyber.trashbin)
        self.assertEqual(digest, digest2, "Digest is not deterministic")
        a_seed, b, trashbin = self.ctx.from_digest(digest)
        self.assertEqual(self.kyber.a_seed, a_seed)
        self.assertEqual(self.kyber.b, b)
        self.assertEqual(self.kyber.trashbin, trashbin)
