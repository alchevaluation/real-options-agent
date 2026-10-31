import unittest

from real_options_agent import CashFlow, discounted_cash_flow


class DCFTests(unittest.TestCase):
    def test_hand_calculated_project(self):
        result = discounted_cash_flow([CashFlow(1, 110), CashFlow(2, 121)], 0.1, 150)
        self.assertAlmostEqual(result.present_value, 200)
        self.assertAlmostEqual(result.npv, 50)
        self.assertEqual(result.initial_investment, 150)

    def test_zero_rate_signed_flows_and_time_zero(self):
        result = discounted_cash_flow([CashFlow(0, -10), CashFlow(1, 70)], 0, 20)
        self.assertEqual(result.npv, 40)

    def test_fractional_time_and_negative_rate(self):
        self.assertAlmostEqual(discounted_cash_flow([CashFlow(0.5, 110)], 0.21).npv, 100)
        self.assertAlmostEqual(discounted_cash_flow([CashFlow(1, 90)], -0.1).npv, 100)

    def test_generator_empty_and_unsorted_flows(self):
        self.assertEqual(discounted_cash_flow([], 0.1, 20).npv, -20)
        flows = (CashFlow(t, 100) for t in [2, 0, 1, 1])
        self.assertAlmostEqual(discounted_cash_flow(flows, 0.1).npv, 100 + 200 / 1.1 + 100 / 1.21)

    def test_invalid_flow_values(self):
        for time, amount in [(-1, 10), (float("nan"), 10), (1, float("inf")), (True, 1), (1, "10")]:
            with self.subTest(time=time, amount=amount), self.assertRaises(ValueError):
                CashFlow(time, amount)

    def test_invalid_rates_and_investments(self):
        for rate in [-1, -2, float("nan"), float("inf"), True, "0.1"]:
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                discounted_cash_flow([], rate)
        for investment in [-1, float("inf"), False]:
            with self.subTest(investment=investment), self.assertRaises(ValueError):
                discounted_cash_flow([], 0.1, investment)

    def test_invalid_flow_type(self):
        with self.assertRaises(ValueError):
            discounted_cash_flow([100], 0.1)

    def test_numerical_range_rejected(self):
        for flow, rate in [(CashFlow(10000, 1), -0.99), (CashFlow(10000, 1), 1), (CashFlow(0, 1e308), 0)]:
            with self.subTest(flow=flow, rate=rate), self.assertRaises(ValueError):
                discounted_cash_flow([flow, flow], rate)
