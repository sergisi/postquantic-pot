import unittest
import random
from src.ecoin import (
    FatContext,
    gotta_go_fat,
    Valued,
    create_valued,
    merchant_spend,
    NonValued,
    create_nonvalued,
)


class TestEcoinProtocol(unittest.TestCase):
    fatctx: FatContext

    def setUp(self):
        # NOTE: this is cached
        self.fatctx = gotta_go_fat()
        super().setUp()

    def test_valued(self):
        valued: Valued = create_valued(self.fatctx)
        m = random.randbytes(32)
        m_enc = merchant_spend(m, valued)
        m_dec = valued.kyb.dec(m_enc)
        self.assertEqual(int.from_bytes(m), m_dec)

    def test_nonvalued(self):
        valued: NonValued = create_nonvalued(self.fatctx)
        m = random.randbytes(32)
        _ = merchant_spend(m, valued)  # NOTE: Let it crash
