"""Provider-independent quota policy regression tests, without an Excelnt account."""
import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from studio.quota_contract import QuotaObservation, QuotaBlocked, preflight_quota

NOW = datetime(2026, 10, 11, 9, 0, tzinfo=timezone.utc)


def fake(worker="A", used=50, weekly=50, protected=True):
    return QuotaObservation(
        worker_alias=worker,
        observed_at=NOW,
        five_hour_used=used,
        five_hour_limit=600,
        weekly_used=weekly,
        weekly_limit=4200,
        five_hour_resets_at=NOW + timedelta(hours=4),
        weekly_resets_at=NOW + timedelta(days=6),
        balance_fallback_disabled=protected,
        auto_topup_disabled=protected,
        paid_overage_disabled=protected,
    )


class QuotaContractTests(unittest.TestCase):
    def verify(self, data=None, worker="A", cost=10, now=NOW):
        return preflight_quota(fake() if data is None else data, worker, cost, now=now)

    def test_safe_included_usage(self):
        self.assertEqual(self.verify(), "READY")

    def test_explicitly_unconnected_is_fail_closed(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=False)

    def test_balance_fallback_must_be_disabled_even_without_topups(self):
        obs = dataclasses.replace(fake(), balance_fallback_disabled=False)
        with self.assertRaises(QuotaBlocked):
            self.verify(data=obs)

    def test_topup_and_paid_overage_must_be_disabled(self):
        for fld in ("auto_topup_disabled", "paid_overage_disabled"):
            with self.subTest(fld=fld):
                with self.assertRaises(QuotaBlocked):
                    self.verify(data=dataclasses.replace(fake(), **{fld: False}))

    def test_80_percent_warning(self):
        self.assertEqual(self.verify(data=fake(used=480), cost=1), "WARNING")

    def test_90_percent_pause(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=fake(used=540))

    def test_request_cost_headroom(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=fake(used=530), cost=15)

    def test_weekly_quota_also_applies(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=fake(weekly=3780), cost=1)

    def test_stale_usage_blocks(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(now=NOW + timedelta(minutes=7))

    def test_expired_reset_blocks(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=dataclasses.replace(fake(), five_hour_resets_at=NOW))

    def test_wrong_account_never_rotates(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=fake(worker="B"))

    def test_unknown_account_rejected(self):
        with self.assertRaises(QuotaBlocked):
            self.verify(data=fake(worker="B"), worker="C")

    def test_boolean_and_nan_costs_rejected(self):
        for cost in (True, float("nan"), 0, -1, float("inf")):
            with self.subTest(cost=cost):
                with self.assertRaises(QuotaBlocked):
                    self.verify(cost=cost)

    def test_naive_timestamp_rejected(self):
        obs = dataclasses.replace(fake(), observed_at=datetime(2026, 10, 11, 9, 0))
        with self.assertRaises(QuotaBlocked):
            self.verify(data=obs)

    def test_separate_workers_have_separate_quota(self):
        self.assertEqual(self.verify(fake("A"), "A"), "READY")
        self.assertEqual(self.verify(fake("B"), "B"), "READY")
        with self.assertRaises(QuotaBlocked):
            self.verify(fake("A", used=540), "A")
        self.assertEqual(self.verify(fake("B"), "B"), "READY")


if __name__ == "__main__":
    unittest.main()
