"""DCF and discrete scenario foundations for a future real-options engine."""

from .dcf import CashFlow, DCFResult, discounted_cash_flow
from .scenarios import (
    PROBABILITY_TOLERANCE,
    Scenario,
    ScenarioAnalysis,
    ScenarioResult,
    evaluate_scenarios,
    expected_monetary_value,
)

__all__ = [
    "CashFlow", "DCFResult", "discounted_cash_flow", "PROBABILITY_TOLERANCE",
    "Scenario", "ScenarioAnalysis", "ScenarioResult", "evaluate_scenarios",
    "expected_monetary_value",
]
