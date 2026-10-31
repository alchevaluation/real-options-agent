"""Run a deterministic example using entirely synthetic data."""

from . import CashFlow, Scenario, evaluate_scenarios


def main() -> None:
    # Each scenario has its own investment, returns and discount rate.
    scenarios = [
        Scenario("downside", 0.25, (CashFlow(1, 40), CashFlow(2, 40)), 100, discount_rate=0.12),
        Scenario("base", 0.50, (CashFlow(1, 70), CashFlow(2, 70)), 100, discount_rate=0.10),
        Scenario("upside", 0.25, (CashFlow(1, 100), CashFlow(2, 100)), 100, discount_rate=0.08),
    ]
    result = evaluate_scenarios(scenarios)
    print("Synthetic project | one cash flow and discount rate per scenario")
    for outcome in result.outcomes:
        print(
            f"{outcome.name}: probability={outcome.probability:.0%}, "
            f"rate={outcome.discount_rate:.0%}, NPV={outcome.dcf.npv:.2f}, "
            f"probability x NPV={outcome.weighted_npv:.2f}"
        )
    print(f"Expected monetary value (EMV): {result.emv:.2f}")
    print(f"NPV standard deviation: {result.standard_deviation:.2f}")
    print(f"Probability of negative NPV: {result.probability_of_loss:.0%}")


if __name__ == "__main__":
    main()
