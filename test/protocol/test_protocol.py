import random
import unittest

from src.protocol import *


def _get_expected_message(price: int, pctx: ProtocolContext) -> bytes:
    key_gen = SHAKE256.new()
    for i, trans in enumerate(pctx):
        if price & (1 << i) != 0:
            blob = trans.blindpk.expected
            key_gen.update(blob)
    return key_gen.read(32)


class TestWholeProtocol(unittest.TestCase):
    pctx: ProtocolContext

    def setUp(self) -> None:
        ctx, ecoin = set_up_ecoins(max_coins=4)
        self.pctx = items_preparation(ctx, ecoin)
        return super().setUp()

    def test_protocol(self):
        price = random.getrandbits(len(self.pctx))
        wallet = create_coins(price, self.pctx)
        blob = customer_spend_coin(price, wallet, self.pctx)
        expected = _get_expected_message(price, self.pctx)
        self.assertEqual(expected, blob)
