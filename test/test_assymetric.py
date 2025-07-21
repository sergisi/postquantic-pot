import unittest

from src import assymetric


class TestAssymetric(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_assymetric_protocol(self):
        ctx = assymetric.get_context()
        A = ctx.random_vector()
        C = ctx.random_vector()
        set_up_data = assymetric.create_merchant(ctx, A, C)
        key_got = assymetric._protocol(set_up_data, ctx)
        # first 8 bytes are not null
        self.assertNotEqual(key_got[:8], bytes(8))
        self.assertEqual(set_up_data.expected, key_got)

    def test_100_times(self):
        for _ in range(100):
            self.test_assymetric_protocol()
