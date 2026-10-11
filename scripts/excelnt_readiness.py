"""Offline-only sanitized Excelnt A/B integration readiness.
Run: python -m scripts.excelnt_readiness (NO HTTP or AI requests).
"""
import json
from studio.excelnt_accounts import ExcelntAccounts, ExcelntIntegrationBlocked


def main() -> int:
    try:
        print(json.dumps({"status": "OFFLINE_ONLY", "workers": ExcelntAccounts().all_readiness()},
                         indent=2, sort_keys=True))
    except ExcelntIntegrationBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
