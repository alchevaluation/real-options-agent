"""Probability-weighted outcomes for mutually exclusive project scenarios.

Each scenario carries its own cash flow: initial investment, dated returns and
discount rate. The expected monetary value (EMV) is the probability-weighted
sum of the scenario NPVs, and the probabilities must add up to one.
"""

from dataclasses import dataclass
from math import fsum, isclose, isfinite, sqrt
from typing import Iterable

from .dcf import CashFlow, DCFResult, _finite_real, discounted_cash_flow

PROBABILITY_TOLERANCE = 1e-9
"""Absolute tolerance accepted when checking that probabilities sum to one."""


@dataclass(frozen=True)
class Scenario:
    """One mutually exclusive outcome with its own complete cash flow.

    ``discount_rate`` is the effective rate per period of this scenario, in
    decimal. It may be left as ``None`` only when a common rate is passed to
    :func:`evaluate_scenarios`; a rate set here always takes precedence.
    """

    name: str
    probability: float
    cash_flows: tuple[CashFlow, ...]
    initial_investment: float = 0.0
    discount_rate: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("scenario name must be nonempty")
        probability = _finite_real(self.probability, "probability")
        investment = _finite_real(self.initial_investment, "initial_investment")
        if not 0 <= probability <= 1:
            raise ValueError("probability must lie between 0 and 1")
        if investment < 0:
            raise ValueError("initial_investment must be nonnegative")
        rate = self.discount_rate
        if rate is not None:
            rate = _finite_real(rate, "discount_rate")
            if rate <= -1:
                raise ValueError("discount_rate must be greater than -1")
        flows = tuple(self.cash_flows)
        if any(not isinstance(flow, CashFlow) for flow in flows):
            raise ValueError("cash_flows must contain CashFlow objects")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "probability", probability)
        object.__setattr__(self, "cash_flows", flows)
        object.__setattr__(self, "initial_investment", investment)
        object.__setattr__(self, "discount_rate", rate)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    probability: float
    discount_rate: float
    dcf: DCFResult

    @property
    def weighted_npv(self) -> float:
        """Contribution of this scenario to the EMV: probability × NPV."""
        return self.probability * self.dcf.npv


@dataclass(frozen=True)
class ScenarioAnalysis:
    outcomes: tuple[ScenarioResult, ...]
    expected_npv: float
    variance: float
    standard_deviation: float
    probability_of_loss: float
    minimum_npv: float
    maximum_npv: float

    @property
    def emv(self) -> float:
        """Expected monetary value: sum of probability × NPV over scenarios."""
        return self.expected_npv


def evaluate_scenarios(
    scenarios: Iterable[Scenario], discount_rate: float | None = None
) -> ScenarioAnalysis:
    """Evaluate an exhaustive scenario set, each with its own cash flow.

    Every scenario is discounted with its own ``discount_rate``; ``discount_rate``
    given here is only a fallback for scenarios that do not define one.
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
    if discount_rate is not None:
        discount_rate = _finite_real(discount_rate, "discount_rate")
    total = fsum(item.probability for item in items)
    if not isclose(total, 1.0, rel_tol=0, abs_tol=PROBABILITY_TOLERANCE):
        raise ValueError(
            f"scenario probabilities must sum to 1 (they sum to {total:.10g})"
        )
    outcomes = []
    for item in items:
        rate = discount_rate if item.discount_rate is None else item.discount_rate
        if rate is None:
            raise ValueError(
                f"scenario {item.name!r} has no discount_rate and no common rate was given"
            )
        outcomes.append(
            ScenarioResult(
                item.name, item.probability / total, rate,
                discounted_cash_flow(item.cash_flows, rate, item.initial_investment),
            )
        )
    outcomes = tuple(outcomes)
    possible = tuple(outcome for outcome in outcomes if outcome.probability > 0)
    try:
        expected = fsum(item.weighted_npv for item in possible)
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


def expected_monetary_value(
    scenarios: Iterable[Scenario], discount_rate: float | None = None
) -> float:
    """EMV = sum(probability_i × NPV_i); probabilities must sum to one."""
    return evaluate_scenarios(scenarios, discount_rate).expected_npv
