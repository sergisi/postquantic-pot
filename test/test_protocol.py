import unittest
from src import ajtai
from src.protocol import AESCyphertext, set_up, Bank, Customer, Protocol
from src.context import Context, get_context, gotta_go_fast_context


class TestProtocolCustomerCreation(unittest.TestCase):
    ctx: Context
    protocol: Protocol
    issuer: Bank
    customer: Customer

    def setUp(self) -> None:
        self.ctx = gotta_go_fast_context()
        self.protocol = set_up(self.ctx, identity="Mr. Burns")
        self.bank = self.protocol.bank
        self.customer = self.protocol.customer
        return super().setUp()


class TestProtocolFast(unittest.TestCase):
    ctx: Context
    protocol: Protocol
    issuer: Bank
    customer: Customer

    def setUp(self) -> None:
        self.ctx = gotta_go_fast_context()
        self.protocol = set_up(self.ctx, identity="Mr. Burns")
        self.bank = self.protocol.bank
        self.customer = self.protocol.customer
        return super().setUp()

    def test_dumb(self):
        """
        I like to test everything and don't know why it fails
        """
        ecoin = self.customer.generate_ecoin(self.bank)
        self.assertTrue(self.customer.spend_ecoin(self.bank, ecoin))
        self.assertEqual("Mr. Burns", self.customer.spend_ecoin(self.bank, ecoin))


class TestProtocolSlow(TestProtocolFast):
    ctx: Context
    protocol: Protocol
    issuer: Bank
    customer: Customer

    def setUp(self) -> None:
        self.ctx = get_context()
        self.protocol = set_up(self.ctx, identity="Mr. Burns")
        self.bank = self.protocol.bank
        self.customer = self.protocol.customer

    def test_initial_main(self):
        ctx = get_context()
        protocol = set_up(ctx, identity="Mr. Burns")
        bank = protocol.bank
        customer = protocol.customer
        pk = customer.pk
        ecoin = customer.generate_ecoin(bank)
        for i in range(200, 500):
            customer = Customer(pk, ctx, repr(i))
            ecoin = customer.generate_ecoin(bank)
            c = customer.spend_ecoin(bank, ecoin)

    @unittest.skip("Skips 200 tests")
    def test_thousand(self):
        bank = self.bank
        pk = self.bank.pk
        ctx = self.ctx
        ecoin = self.customer.generate_ecoin(bank)
        self.assertTrue(self.customer.spend_ecoin(bank, ecoin))
        self.assertEqual(
            "Mr. Burns", self.customer.spend_ecoin(bank, ecoin), self.customer
        )
        for i in range(200):
            customer = Customer(pk, ctx, repr(i))
            self.assertIn(customer.id_pk, bank.identity_db)
            self.assertEqual(repr(i), bank.identity_db[customer.id_pk])
            ecoin = customer.generate_ecoin(bank)
            self.assertTrue(customer.spend_ecoin(bank, ecoin))
            c = customer.spend_ecoin(bank, ecoin)
            self.assertEqual(customer.identity, c)
