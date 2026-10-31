"""Probability-weighted outcomes for mutually exclusive project scenarios."""

from dataclasses import dataclass
from math import fsum, isclose, isfinite, sqrt
from typing import Iterable

from .dcf import CashFlow, DCFResult, _finite_real, discounted_cash_flow


@dataclass(frozen=True)
class Scenario:
    name: str
    probability: float
    cash_flows: tuple[CashFlow, ...]
    initial_investment: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("scenario name must be nonempty")
        probability = _finite_real(self.probability, "probability")
        investment = _finite_real(self.initial_investment, "initial_investment")
        if not 0 <= probability <= 1:
            raise ValueError("probability must lie between 0 and 1")
        if investment < 0:
            raise ValueError("initial_investment must be nonnegative")
        flows = tuple(self.cash_flows)
        if any(not isinstance(flow, CashFlow) for flow in flows):
            raise ValueError("cash_flows must contain CashFlow objects")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "probability", probability)
        object.__setattr__(self, "cash_flows", flows)
        object.__setattr__(self, "initial_investment", investment)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    probability: float
    dcf: DCFResult


@dataclass(frozen=True)
class ScenarioAnalysis:
    outcomes: tuple[ScenarioResult, ...]
    expected_npv: float
    variance: float
    standard_deviation: float
    probability_of_loss: float
    minimum_npv: float
    maximum_npv: float


def evaluate_scenarios(
    scenarios: Iterable[Scenario], discount_rate: float
) -> ScenarioAnalysis:
    """Evaluate an exhaustive scenario set with a common discount rate.

    Probabilities must sum to one within absolute tolerance 1e-9. Accepted
    rounding errors are normalized; zero-probability outcomes are retained
    but excluded from the minimum and maximum possible NPVs.
    """
    items = tuple(scenarios)
    if not items:
        raise ValueError("at least one scenario is required")
    if any(not isinstance(item, Scenario) for item in items):
        raise ValueError("scenarios must contain Scenario objects")
    if len({item.name for item in items}) != len(items):
        raise ValueError("scenario names must be unique")
    total = fsum(item.probability for item in items)
    if not isclose(total, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError("scenario probabilities must sum to 1")
    outcomes = tuple(
        ScenarioResult(
            item.name, item.probability / total,
            discounted_cash_flow(item.cash_flows, discount_rate, item.initial_investment),
        )
        for item in items
    )
    possible = tuple(outcome for outcome in outcomes if outcome.probability > 0)
    try:
        expected = fsum(item.probability * item.dcf.npv for item in possible)
        variance = fsum(
            item.probability * (item.dcf.npv - expected) ** 2 for item in possible
        )
    except OverflowError as exc:
        raise ValueError("scenario moments exceed the numerical range") from exc
    if not isfinite(expected) or not isfinite(variance):
        raise ValueError("scenario moments exceed the numerical range")
    return ScenarioAnalysis(
        outcomes, expected, variance, sqrt(variance),
        fsum(item.probability for item in possible if item.dcf.npv < 0),
        min(item.dcf.npv for item in possible),
        max(item.dcf.npv for item in possible),
    )
