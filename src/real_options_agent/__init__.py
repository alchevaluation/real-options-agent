"""DCF and discrete scenario foundations for a future real-options engine."""

from .dcf import CashFlow, DCFResult, discounted_cash_flow
from .scenarios import Scenario, ScenarioAnalysis, ScenarioResult, evaluate_scenarios

__all__ = [
    "CashFlow", "DCFResult", "discounted_cash_flow", "Scenario",
    "ScenarioAnalysis", "ScenarioResult", "evaluate_scenarios",
]
