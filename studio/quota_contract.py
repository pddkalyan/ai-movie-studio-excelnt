"""Read-only quota policy contract. No Excelnt API implementation or balance access.

Provenance: ChatGPT GPT-6, EX-0001. Never switch accounts when exhausted.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Protocol
import math


class QuotaBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class QuotaObservation:
    worker_alias: str
    observed_at: datetime
    five_hour_used: float
    five_hour_limit: float
    weekly_used: float
    weekly_limit: float
    five_hour_resets_at: datetime
    weekly_resets_at: datetime
    # This provider-enforced flag is NOT available from user screenshots.
    balance_fallback_disabled: bool = False
    auto_topup_disabled: bool = False
    paid_overage_disabled: bool = False


class QuotaSource(Protocol):
    def observe(self, worker_alias: str) -> QuotaObservation:
        """Return trusted, authenticated account-specific official usage telemetry."""


def preflight_quota(
    observation: QuotaObservation | None,
    worker_alias: str,
    worst_case_units: float,
    *,
    now: datetime | None = None,
) -> str:
    """Return READY or WARNING, else fail closed before ANY inference call.

    This is NOT wired into a VS Code extension or any API. An actual caller must
    verify provider-enforced caps and durably journal a request before sending.
    """
    if worker_alias not in ("A", "B"):
        raise QuotaBlocked("Unassigned worker; no account switching")
    if observation is None or not isinstance(observation, QuotaObservation):
        raise QuotaBlocked("No verified official Excelnt quota telemetry")
    if observation.worker_alias != worker_alias:
        raise QuotaBlocked("Wrong account quota")
    if (observation.balance_fallback_disabled is not True or
            observation.auto_topup_disabled is not True or
            observation.paid_overage_disabled is not True):
        raise QuotaBlocked("Balance-funded fallback and paid usage not proven disabled")
    current = now if now is not None else datetime.now(timezone.utc)
    times = (current, observation.observed_at, observation.five_hour_resets_at,
             observation.weekly_resets_at)
    if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None
           for t in times):
        raise QuotaBlocked("Timezone-aware provider timestamps required")
    if (current - observation.observed_at > timedelta(minutes=5) or
            observation.observed_at > current + timedelta(seconds=30) or
            observation.five_hour_resets_at <= current or
            observation.weekly_resets_at <= current):
        raise QuotaBlocked("Missing, stale or expired quota observation")
    values = (observation.five_hour_used, observation.five_hour_limit,
              observation.weekly_used, observation.weekly_limit, worst_case_units)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) for v in values):
        raise QuotaBlocked("Invalid numeric quota fields")
    u5, l5, uw, lw, cost = values
    if (l5 <= 0 or lw <= 0 or cost <= 0 or
            u5 < 0 or uw < 0 or u5 > l5 or uw > lw):
        raise QuotaBlocked("Invalid usage or unbounded estimated request")
    if ((u5 + cost) > 0.9 * l5 or (uw + cost) > 0.9 * lw or
            u5 >= 0.9 * l5 or uw >= 0.9 * lw):
        raise QuotaBlocked("Approaching included allowance limit; checkpoint and wait")
    return "WARNING" if u5 >= 0.8 * l5 or uw >= 0.8 * lw else "READY"
