import unittest
from src.ecoin.kyber import kyber_key_gen, Kyber
from src.context.kyber_context import KyberContext, get_kyber_context
from src.poly import Poly, PolyVec, PolyMat
import functools as fun
import dataclasses as dto
import random


class TestKyber(unittest.TestCase):
    ctx: KyberContext
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
