import unittest
from src.context import Context, get_context, gotta_go_fast_context
from src.falcon import MyFalcon


class TestFalcon(unittest.TestCase):

    def setUp(self) -> None:
        self.ctx = gotta_go_fast_context()
        self.falcon = MyFalcon(self.ctx)
        return super().setUp()

    def test_falcon_signature(self):
        m = self.ctx.r_small(200)
        s = self.falcon.my_sign(m)
        norm_sign = sum(coef**2 for coef in self.ctx.collapse_even(s[0]))
        norm_sign += sum(coef**2 for coef in self.ctx.collapse_even(s[1]))
        h_poly = self.ctx.ZpxQ(self.falcon.h)
        s0 = s[0]
        s1 = s[1]
        self.assertLessEqual(norm_sign, self.falcon.signature_bound)
        self.assertEqual(m - h_poly * s1, s0)

    def test_A_matrix_mult_is_correct(self):
        m = self.ctx.r_small(200)
        s = self.falcon.my_sign(m)
        norm_sign = sum(coef**2 for coef in self.ctx.collapse_even(s[0]))
        norm_sign += sum(coef**2 for coef in self.ctx.collapse_even(s[1]))
        h_poly = self.ctx.ZpxQ(self.falcon.h)
        s0 = s[0]
        s1 = s[1]
        self.assertEqual(self.falcon.A[0], 1)
        self.assertEqual(self.falcon.A[1], h_poly)
        self.assertEqual((self.falcon.A * s), s0 + h_poly * s1)
        self.assertEqual(m - h_poly * s1, s0)

    def test_falcon_sign_random_then_verify(self):
        m = self.ctx.r_small(200)
        s = self.falcon.my_sign(m)
        self.assertTrue(self.falcon.my_verify(m, s))


@unittest.skip("Its really slow, and TestFalcon should be ok.")
class TestSlowFalcon(unittest.TestCase):

    def setUp(self) -> None:
        self.ctx = get_context()
        self.falcon = MyFalcon(self.ctx)
        return super().setUp()

    def test_falcon_signature(self):
        m = self.ctx.r_small(200)
        s = self.falcon.my_sign(m)
        norm_sign = sum(coef**2 for coef in self.ctx.collapse_even(s[0]))
        norm_sign += sum(coef**2 for coef in self.ctx.collapse_even(s[1]))
        h_poly = self.ctx.ZpxQ(self.falcon.h)
        s0 = s[0]
        s1 = s[0]
        self.assertLessEqual(norm_sign, self.falcon.signature_bound)
        self.assertEqual(m - h_poly * s1, s0)

    def test_falcon_sign_random_then_verify(self):
        m = self.ctx.r_small(200)
        s = self.falcon.my_sign(m)
        self.assertTrue(self.falcon.my_verify(m, s))
