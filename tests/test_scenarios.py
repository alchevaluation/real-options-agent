import unittest

from real_options_agent import CashFlow, Scenario, evaluate_scenarios, expected_monetary_value


def outcome(name, probability, npv):
    return Scenario(name, probability, (CashFlow(0, npv),))


class ScenarioTests(unittest.TestCase):
    def test_hand_calculated_distribution(self):
        result = evaluate_scenarios([outcome("loss", 0.25, -20), outcome("gain", 0.75, 60)], 0)
        self.assertEqual(result.expected_npv, 40)
        self.assertEqual(result.variance, 1200)
        self.assertAlmostEqual(result.standard_deviation, 1200 ** 0.5)
        self.assertEqual(result.probability_of_loss, 0.25)
        self.assertEqual((result.minimum_npv, result.maximum_npv), (-20, 60))

    def test_investment_discounting_and_generator(self):
        scenarios = (Scenario("only", 1, [CashFlow(1, 110)], 100) for _ in range(1))
        result = evaluate_scenarios(scenarios, 0.1)
        self.assertAlmostEqual(result.expected_npv, 0)
        self.assertEqual(result.variance, 0)

    def test_break_even_is_not_loss(self):
        self.assertEqual(evaluate_scenarios([outcome("zero", 1, 0)], 0).probability_of_loss, 0)

    def test_zero_probability_excluded_from_extrema(self):
        result = evaluate_scenarios([outcome("impossible", 0, -1000), outcome("possible", 1, 20)], 0)
        self.assertEqual(result.minimum_npv, 20)
        self.assertEqual(result.maximum_npv, 20)
        self.assertEqual(len(result.outcomes), 2)

    def test_rounding_normalized(self):
        result = evaluate_scenarios([outcome("a", 0.5, 10), outcome("b", 0.5000000001, 10)], 0)
        self.assertAlmostEqual(sum(item.probability for item in result.outcomes), 1)
        self.assertAlmostEqual(result.expected_npv, 10)

    def test_invalid_scenario_sets(self):
        sets = [[], [outcome("a", 0, 0)], [outcome("a", 0.9, 1)],
                [outcome("a", 1, 1), outcome("b", 1, 2)],
                [outcome("same", 0.5, 1), outcome(" same ", 0.5, 2)], [42]]
        for scenarios in sets:
            with self.subTest(scenarios=scenarios), self.assertRaises(ValueError):
                evaluate_scenarios(scenarios, 0)

    def test_invalid_scenario_fields(self):
        for probability in [-0.1, 1.1, float("nan"), True]:
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                outcome("a", probability, 0)
        for name in ["", " ", None]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                outcome(name, 1, 0)
        with self.assertRaises(ValueError):
            Scenario("a", 1, (10,))
        with self.assertRaises(ValueError):
            Scenario("a", 1, (), -10)

    def test_cash_flow_input_is_frozen_snapshot(self):
        flows = [CashFlow(1, 10)]
        scenario = Scenario("a", 1, flows)
        flows.clear()
        self.assertEqual(len(scenario.cash_flows), 1)

    def test_invalid_rate_propagates(self):
        with self.assertRaises(ValueError):
            evaluate_scenarios([outcome("a", 1, 1)], -1)

    def test_numerical_range_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_scenarios([outcome("a", 0.5, -1e308), outcome("b", 0.5, 1e308)], 0)


class PerScenarioCashFlowTests(unittest.TestCase):
    """Each scenario carries its own investment, returns and discount rate."""

    def test_hand_calculated_emv_with_different_rates(self):
        # low: 100 invested, 110 at t=1 discounted at 10% -> NPV 0
        # high: 50 invested, 120 at t=1 discounted at 20% -> NPV 50
        scenarios = [
            Scenario("low", 0.4, (CashFlow(1, 110),), 100, discount_rate=0.10),
            Scenario("high", 0.6, (CashFlow(1, 120),), 50, discount_rate=0.20),
        ]
        result = evaluate_scenarios(scenarios)
        self.assertAlmostEqual(result.outcomes[0].dcf.npv, 0)
        self.assertAlmostEqual(result.outcomes[1].dcf.npv, 50)
        self.assertEqual(result.outcomes[0].discount_rate, 0.10)
        self.assertEqual(result.outcomes[1].discount_rate, 0.20)
        self.assertAlmostEqual(result.outcomes[1].weighted_npv, 30)
        self.assertAlmostEqual(result.emv, 30)
        self.assertEqual(result.emv, result.expected_npv)
        self.assertAlmostEqual(expected_monetary_value(scenarios), 30)

    def test_scenario_rate_takes_precedence_over_common_rate(self):
        own = Scenario("own", 0.5, (CashFlow(1, 100),), 0, discount_rate=0.0)
        shared = Scenario("shared", 0.5, (CashFlow(1, 100),), 0)
        result = evaluate_scenarios([own, shared], discount_rate=1.0)
        self.assertEqual(result.outcomes[0].dcf.npv, 100)
        self.assertEqual(result.outcomes[1].dcf.npv, 50)
        self.assertEqual(result.outcomes[1].discount_rate, 1.0)

    def test_missing_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_scenarios([Scenario("a", 1, (CashFlow(1, 1),))])

    def test_invalid_scenario_rate(self):
        for rate in [-1, float("nan"), float("inf"), True, "0.1"]:
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                Scenario("a", 1, (), 0, discount_rate=rate)

    def test_probabilities_not_summing_to_one_report_total(self):
        scenarios = [
            Scenario("a", 0.3, (), 0, discount_rate=0.1),
            Scenario("b", 0.3, (), 0, discount_rate=0.1),
        ]
        with self.assertRaises(ValueError) as ctx:
            expected_monetary_value(scenarios)
        self.assertIn("0.6", str(ctx.exception))
