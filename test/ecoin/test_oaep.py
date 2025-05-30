from src.ecoin import oaep
import random

import unittest


class TestOAEP(unittest.TestCase):

    def test_oaep_symmetric(self):
        m = random.randbytes(32)
        r = random.randbytes(32)
        x, y = oaep.enc(m, r)
        m_, r_ = oaep.dec(x, y)
        self.assertEqual(len(m), len(m_))
        self.assertEqual(m, m_)
        self.assertEqual(r, r_)

    def test_oaep_different_byte_size(self):
        m = random.randbytes(736)
        r = random.randbytes(32)
        x, y = oaep.enc(m, r)
        m_, r_ = oaep.dec(x, y)
        self.assertEqual(len(m), len(m_))
        self.assertEqual(m, m_)
        self.assertEqual(r, r_)
