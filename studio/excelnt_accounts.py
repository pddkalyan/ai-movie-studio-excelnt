"""Offline-only Excelnt A/B secret-slot and gateway integration readiness.

Provenance: ChatGPT GPT-6, EX-0006. Never makes an HTTP/model request.
Verified source: owner-shared Excelnt API Keys page, 2026-10-11.
"""
from __future__ import annotations

import hmac
import os
from dataclasses import asdict, dataclass
from typing import Mapping, Protocol
from urllib.parse import urlsplit

GATEWAY_BASE_URL = "https://excelnt.ai/v1"
KEY_SLOTS = {"A": "EXCELNT_WORKER_A_API_KEY", "B": "EXCELNT_WORKER_B_API_KEY"}


class ExcelntIntegrationBlocked(RuntimeError):
    """Stop: do not send inference, buy usage, switch accounts, or guess routes."""


def _worker(alias: str) -> str:
    if type(alias) is not str or alias not in KEY_SLOTS:
        raise ExcelntIntegrationBlocked("Unknown worker alias; only A and B are supported")
    return alias


def _check_gateway_origin(url: str) -> None:
    try:
        parsed = urlsplit(url)
        safe = (url == GATEWAY_BASE_URL and parsed.scheme == "https" and
                parsed.hostname == "excelnt.ai" and parsed.netloc == "excelnt.ai" and
                parsed.path == "/v1" and not parsed.query and not parsed.fragment)
    except (TypeError, ValueError):
        safe = False
    if not safe:
        raise ExcelntIntegrationBlocked("Only the documented Excelnt HTTPS API base URL is permitted")


def _valid_secret(value: object) -> bool:
    # Keys are entirely private and not printed; we don't assume their prefix/length.
    return (type(value) is str and bool(value) and value == value.strip() and
            not any(ord(char) < 33 or ord(char) == 127 for char in value) and
            value not in {"your-key", "YOUR_API_KEY", "placeholder", "null"})


@dataclass(frozen=True)
class Readiness:
    worker_alias: str
    credential_present: bool
    api_base_documented: bool
    request_schema_verified: bool
    authenticated_quota_source_verified: bool
    provider_balance_fallback_disabled_verified: bool
    allowed_for_live_requests: bool

    def sanitized(self) -> dict:
        return asdict(self)


class SupportedExcelntGateway(Protocol):
    """Placeholder for a future *separately reviewed* supported API connector.

    Not implemented because request paths, response schema and hard spend caps
    are NOT documented in the currently available Excelnt sources.
    """

    def request_for_worker(self, alias: str, payload: object) -> object: ...


class ExcelntAccounts:
    """Private credential-slot checker; cannot send model requests.

    Credential rotation is a **same-account key replacement**, performed via
    a private environment/secret manager after pausing that worker. It does
    not rotate accounts or replenish usage windows.
    """

    def __init__(self, environment: Mapping[str, str] | None = None, *, base_url: str = GATEWAY_BASE_URL):
        _check_gateway_origin(base_url)
        self._environment = environment if environment is not None else os.environ

    def credential_present(self, alias: str) -> bool:
        alias = _worker(alias)
        secret = self._environment.get(KEY_SLOTS[alias])
        return _valid_secret(secret)

    def _check_distinct(self) -> None:
        a = self._environment.get(KEY_SLOTS["A"])
        b = self._environment.get(KEY_SLOTS["B"])
        if _valid_secret(a) and _valid_secret(b) and hmac.compare_digest(a, b):
            raise ExcelntIntegrationBlocked("Both worker slots point to one credential; account separation unverified")

    def readiness(self, alias: str) -> Readiness:
        alias = _worker(alias)
        self._check_distinct()
        return Readiness(
            worker_alias=alias,
            credential_present=self.credential_present(alias),
            api_base_documented=True,
            request_schema_verified=False,
            authenticated_quota_source_verified=False,
            provider_balance_fallback_disabled_verified=False,
            allowed_for_live_requests=False,
        )

    def all_readiness(self) -> dict[str, dict]:
        # No key contents, key prefix, key length, fingerprint, account email,
        # profile name, billing identifier or guessed model route is exposed.
        return {alias: self.readiness(alias).sanitized() for alias in KEY_SLOTS}

    def send_model_request(self, alias: str, request: object) -> None:
        _worker(alias)
        raise ExcelntIntegrationBlocked(
            "Excelnt model calls are disabled: official request protocol, account-scoped "
            "quota source, and provider-enforced no-balance-fallback are not verified"
        )

    def rotate_key(self, alias: str, replacement: str) -> None:
        _worker(alias)
        raise ExcelntIntegrationBlocked(
            "Credential replacement must happen in a private secret manager while "
            "the same authorized worker is paused; this module never mutates keys"
        )
