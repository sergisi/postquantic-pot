import random
import unittest

from src.protocol import *

def _get_expected_message(price: int, pctx: ProtocolContext) -> bytes:
    key_gen = SHAKE256.new()
    for i in range(pctx.max_coins):
        if price & (1 << i) != 0:
            blob = pctx.blindpk[i].expected
            key_gen.update(blob)
    return key_gen.read(32)
            

class TestWholeProtocol(unittest.TestCase):
    pctx: ProtocolContext

    def setUp(self) -> None:
        self.pctx = set_up_pctx()
        return super().setUp()

    def test_protocol(self):
        price = random.getrandbits(self.pctx.max_coins)
        wallet = create_coins(price, self.pctx)
        blob = customer_spend_coin(price, wallet, self.pctx)
        expected = _get_expected_message(price, self.pctx)
        self.assertEqual(expected, blob)

    
