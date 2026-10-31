"""Discount signed, explicitly dated cash flows in a single currency."""

from dataclasses import dataclass
from math import fsum, isfinite
from numbers import Real
from typing import Iterable


def _finite_real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


@dataclass(frozen=True)
class CashFlow:
    """An amount at a nonnegative time, measured in rate periods."""

    time: float
    amount: float

    def __post_init__(self) -> None:
        time = _finite_real(self.time, "time")
        amount = _finite_real(self.amount, "amount")
        if time < 0:
            raise ValueError("time must be nonnegative")
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "amount", amount)


@dataclass(frozen=True)
class DCFResult:
    present_value: float
    initial_investment: float
    npv: float


def discounted_cash_flow(
    cash_flows: Iterable[CashFlow],
    discount_rate: float,
    initial_investment: float = 0.0,
) -> DCFResult:
    """PV = sum(CF_t / (1+r)**t); NPV = PV - investment at time zero.

    The effective rate and times must use the same period. Fractional times,
    negative cash flows, and rates strictly greater than -1 are supported.
    """
    rate = _finite_real(discount_rate, "discount_rate")
    investment = _finite_real(initial_investment, "initial_investment")
    if rate <= -1:
        raise ValueError("discount_rate must be greater than -1")
    if investment < 0:
        raise ValueError("initial_investment must be nonnegative")
    values = []
    try:
        for flow in cash_flows:
            if not isinstance(flow, CashFlow):
                raise ValueError("cash_flows must contain CashFlow objects")
            values.append(flow.amount / (1.0 + rate) ** flow.time)
        pv = fsum(values)
        npv = pv - investment
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("cash flows and rate exceed the numerical range") from exc
    if not isfinite(pv) or not isfinite(npv):
        raise ValueError("cash flows and rate exceed the numerical range")
    return DCFResult(pv, investment, npv)
