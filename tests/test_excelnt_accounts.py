"""No-network, no-paid, no-real-key EX-0006 gateway/secret-slot regression."""
from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import unittest
from unittest.mock import patch

from studio.excelnt_accounts import (
    ExcelntAccounts, ExcelntIntegrationBlocked, GATEWAY_BASE_URL, KEY_SLOTS
)


class ExcelntAccountSlotsTests(unittest.TestCase):
    def setUp(self):
        self.env = {KEY_SLOTS["A"]: "synthetic-A-only", KEY_SLOTS["B"]: "synthetic-B-only"}

    def test_gateway_root_documented_but_no_route_is_assumed(self):
        self.assertEqual(GATEWAY_BASE_URL, "https://excelnt.ai/v1")
        self.assertNotIn("/chat/completions", GATEWAY_BASE_URL)
        self.assertNotIn("/responses", GATEWAY_BASE_URL)

    def test_distinct_separate_slots_have_no_live_access(self):
        states = ExcelntAccounts(self.env).all_readiness()
        self.assertEqual(set(states), {"A", "B"})
        self.assertTrue(states["A"]["credential_present"])
        self.assertTrue(states["B"]["credential_present"])
        for x in states.values():
            self.assertTrue(x["api_base_documented"])
            self.assertFalse(x["request_schema_verified"])
            self.assertFalse(x["authenticated_quota_source_verified"])
            self.assertFalse(x["provider_balance_fallback_disabled_verified"])
            self.assertFalse(x["allowed_for_live_requests"])

    def test_no_credentials_is_not_active(self):
        states = ExcelntAccounts({}).all_readiness()
        self.assertFalse(states["A"]["credential_present"])
        self.assertFalse(states["B"]["credential_present"])
        self.assertFalse(states["A"]["allowed_for_live_requests"])

    def test_worker_a_only_never_implies_b_auth(self):
        states = ExcelntAccounts({KEY_SLOTS["A"]:"only-worker-A"}).all_readiness()
        self.assertTrue(states["A"]["credential_present"])
        self.assertFalse(states["B"]["credential_present"])

    def test_reuse_of_one_key_in_both_slots_is_rejected(self):
        env = {KEY_SLOTS["A"]:"same-private-secret", KEY_SLOTS["B"]:"same-private-secret"}
        with self.assertRaises(ExcelntIntegrationBlocked):
            ExcelntAccounts(env).all_readiness()

    def test_worker_names_are_strict_and_no_auto_extra_account(self):
        c = ExcelntAccounts(self.env)
        for name in ("C", "", "worker/A", None, 1, "../A"):
            with self.subTest(name=name), self.assertRaises(ExcelntIntegrationBlocked):
                c.readiness(name)

    def test_bad_url_rejected_including_userinfo_query_port_and_http(self):
        for url in ("http://excelnt.ai/v1", "https://excelnt.ai:443/v1",
                    "https://evil.test/v1", "https://user:secret@excelnt.ai/v1",
                    "https://excelnt.ai/v1?secret=1", "https://excelnt.ai/v1#fragment",
                    "https://excelnt.ai/v1/chat/completions", "https://excelnt.ai.evil/v1"):
            with self.subTest(url=url), self.assertRaises(ExcelntIntegrationBlocked):
                ExcelntAccounts(self.env, base_url=url)

    def test_synthetic_keys_never_logged_in_sanitized_status(self):
        data=json.dumps(ExcelntAccounts(self.env).all_readiness())
        for secret in self.env.values():
            self.assertNotIn(secret, data)
        self.assertNotIn("key_length", data)
        self.assertNotIn("key_prefix", data)

    def test_whitespace_control_and_placeholder_keys_invalid(self):
        for v in ("", " key", "key\n", "a\tb", "placeholder", "your-key", "YOUR_API_KEY", "null"):
            state=ExcelntAccounts({KEY_SLOTS["A"]:v}).readiness("A")
            self.assertFalse(state.credential_present)

    def test_no_send_even_with_both_synthetic_keys_and_complete_payload(self):
        c=ExcelntAccounts(self.env)
        with patch.object(socket, "create_connection", side_effect=AssertionError("NETWORK")):
            for alias in ("A", "B"):
                with self.assertRaises(ExcelntIntegrationBlocked):
                    c.send_model_request(alias, {"model":"some-model", "prompt":"hello"})

    def test_key_rotation_must_be_out_of_band(self):
        c=ExcelntAccounts(self.env)
        with self.assertRaises(ExcelntIntegrationBlocked):
            c.rotate_key("A", "another-credential")
        self.assertEqual(self.env[KEY_SLOTS["A"]], "synthetic-A-only")

    def test_code_does_not_export_private_env_or_write_files(self):
        c=ExcelntAccounts(self.env)
        with self.assertRaises(ExcelntIntegrationBlocked):
            c.send_model_request("A", {})
        self.assertEqual(self.env[KEY_SLOTS["B"]], "synthetic-B-only")

    def test_readiness_cli_sanitized_in_no_credentials_environment(self):
        from scripts.excelnt_readiness import main
        buffer=io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(buffer):
            result=main()
        self.assertEqual(result,0)
        data=json.loads(buffer.getvalue())
        self.assertEqual(data["status"],"OFFLINE_ONLY")
        self.assertFalse(data["workers"]["A"]["credential_present"])

    def test_readiness_cli_private_slots_have_boolean_only(self):
        from scripts.excelnt_readiness import main
        buffer=io.StringIO()
        with patch.dict(os.environ,self.env,clear=True),contextlib.redirect_stdout(buffer):
            self.assertEqual(main(),0)
        data=json.loads(buffer.getvalue())
        self.assertTrue(data["workers"]["B"]["credential_present"])
        self.assertNotIn("synthetic",buffer.getvalue())

    def test_invalid_duplicate_slot_from_env_reports_safe_error(self):
        from scripts.excelnt_readiness import main
        env={KEY_SLOTS["A"]:"same", KEY_SLOTS["B"]:"same"}
        buffer=io.StringIO()
        with patch.dict(os.environ,env,clear=True),contextlib.redirect_stdout(buffer):
            self.assertEqual(main(),1)
        self.assertIn("BLOCKED", buffer.getvalue())
        self.assertNotIn('"same"', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
