"""Run a deterministic example using entirely synthetic data."""

from . import CashFlow, Scenario, evaluate_scenarios


def main() -> None:
    scenarios = [
        Scenario("downside", 0.25, (CashFlow(1, 40), CashFlow(2, 40)), 100),
        Scenario("base", 0.50, (CashFlow(1, 70), CashFlow(2, 70)), 100),
        Scenario("upside", 0.25, (CashFlow(1, 100), CashFlow(2, 100)), 100),
    ]
    result = evaluate_scenarios(scenarios, discount_rate=0.10)
    print("Synthetic project | effective annual discount rate: 10%")
    for outcome in result.outcomes:
        print(f"{outcome.name}: probability={outcome.probability:.0%}, NPV={outcome.dcf.npv:.2f}")
    print(f"Expected NPV: {result.expected_npv:.2f}")
    print(f"NPV standard deviation: {result.standard_deviation:.2f}")
    print(f"Probability of negative NPV: {result.probability_of_loss:.0%}")


if __name__ == "__main__":
    main()
