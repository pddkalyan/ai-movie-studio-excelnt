"""Offline EX-0005 checks for the new development branch / release workflow.

No Excelnt network requests, no GitHub mutations, and no secrets.
"""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BranchAndGatewayPolicyTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_ci_runs_for_main_and_develop(self):
        yaml = self.read(".github/workflows/phase0_offline_ci.yml")
        self.assertIn("  push:\n    branches: [main, develop]", yaml)
        self.assertIn("  pull_request:\n    branches: [main, develop]", yaml)
        self.assertIn("contents: read", yaml)
        self.assertIn("persist-credentials: false", yaml)

    def test_release_branch_is_separate_from_integration(self):
        text = self.read("docs/BRANCHING.md")
        self.assertIn("main | Stable release", text)
        self.assertIn("develop | Tested integration", text)
        self.assertIn("develop -> main", text)
        self.assertIn("No automated merges", text)

    def test_no_provider_key_or_model_call_in_workflow(self):
        yaml = self.read(".github/workflows/phase0_offline_ci.yml")
        for token in ("EXCELNT_API_KEY", "secrets.", "curl -", "irm ", "model.generate"):
            self.assertNotIn(token, yaml)

    def test_gateway_is_base_url_not_inferred_api_route(self):
        text = self.read("docs/EXCELNT_API_EVIDENCE.md")
        self.assertIn("https://excelnt.ai/v1", text)
        self.assertIn("0/25 active keys", text)
        self.assertIn("Unverified: GET /models", text)
        self.assertIn("never", text.lower())

    def test_balance_fallback_remains_a_mandatory_gate(self):
        gate = self.read("docs/EXCELNT_GATE.md")
        quota = self.read("studio/quota_contract.py")
        self.assertIn("Balance funds API usage once the plan allowance runs out", gate)
        self.assertIn("balance_fallback_disabled: bool = False", quota)

    def test_provenance_registry_is_valid_jsonl(self):
        entries = [json.loads(line) for line in
                   self.read("PROVENANCE_REGISTRY.jsonl").splitlines() if line]
        self.assertGreaterEqual(len(entries), 18)
        files = {x["file"] for x in entries}
        for f in ("docs/BRANCHING.md", "docs/EXCELNT_API_EVIDENCE.md",
                  "tests/test_development_workflow.py"):
            self.assertIn(f, files)


if __name__ == "__main__":
    unittest.main()
