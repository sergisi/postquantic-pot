import unittest
from src.context import Context, get_kyber_context
import random


class TestDigest(unittest.TestCase):
    ctx: Context[None]

    def setUp(self):
        self.ctx = get_kyber_context()

    def test_digest(self):
        a_seed = random.randbytes(32)
        b = self.ctx.random_vector()
        trashbin = bytes([0] * self.ctx.k)
        blob = self.ctx.digest(a_seed, b, trashbin)
        print(len(blob))
        a_got, b_got, trashbin_got = self.ctx.from_digest(blob)
        self.assertEqual(a_seed, a_got)
        self.assertEqual(b, b_got)
        self.assertEqual(trashbin, trashbin_got)

    def test_fromdigest(self):
        blob = random.randbytes(1532)
        a_got, b_got, trashbin_got = self.ctx.from_digest(blob)
        blob_got = self.ctx.digest(a_got, b_got, trashbin_got)
        self.assertEqual(blob, blob_got)
