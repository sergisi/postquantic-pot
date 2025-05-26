import unittest
import pdb
from src.ecoin.dilithium import Dilithium, dilithium_key_gen, collapse_bits
from src.context import (
    Context,
    DilithiumExtra,
    get_dilithium_context,
)
from src.poly import Poly, PolyVec, PolyMat
import functools as fun
import dataclasses as dto
import random


class TestDilithium(unittest.TestCase):
    ctx: Context[DilithiumExtra]
    dilithium: Dilithium

    def setUp(self):
        self.ctx = get_dilithium_context()
        self.dilithium = dilithium_key_gen(self.ctx)
        super().setUp()

    def test_matrix_seeded(self):
        mat = self.ctx.random_matrix(seed=b'12345')
        mat2 = self.ctx.random_matrix(seed=b'12345')
        self.assertEqual(mat, mat2)

    def test_collapse_bits(self):
        z = self.ctx.random_vector()
        z_high = self.dilithium.decompose(z, self.dilithium.double_gamma2)[1]
        z_bits = collapse_bits(z_high)
        self.assertNotEqual(z_bits, 0)

    def test_hash_works(self):
        """
        Check if hash is deterministic.
        """
        m = random.getrandbits(256)
        w = random.getrandbits(256)
        first = self.dilithium.hash_to_point(m, w)
        snd = self.dilithium.hash_to_point(m, w)
        self.assertEqual(first, snd)

    def test_signature(self):
        message = random.getrandbits(256)
        sig = self.dilithium.sign(message)
        self.assertTrue(self.dilithium.verify(message, sig))
        self.assertFalse(self.dilithium.verify(message + 10, sig))

    @unittest.skip("Too many cases")
    def test_signature_hundred(self):
        for _ in range(100):
            message = random.getrandbits(256)
            sig = self.dilithium.sign(message)
            self.assertTrue(self.dilithium.verify(message, sig))
            self.assertFalse(self.dilithium.verify(message + 10, sig))

    def test_digest_and_from(self):
        digest = self.ctx.digest(self.dilithium.a_seed, self.dilithium.b, self.dilithium.trashbin)
        digest2 = self.ctx.digest(self.dilithium.a_seed, self.dilithium.b, self.dilithium.trashbin)
        self.assertEqual(digest, digest2, "Digest is not deterministic")
        a_seed, b, trashbin_got = self.ctx.from_digest(digest)
        self.assertEqual(self.dilithium.a_seed, a_seed)
        self.assertEqual(self.dilithium.b, b)
        self.assertEqual(self.dilithium.trashbin, trashbin_got)

