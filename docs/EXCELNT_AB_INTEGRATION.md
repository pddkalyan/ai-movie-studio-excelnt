# Excelnt accounts A and B — safe integration checklist (EX-0006)

*Creator: ChatGPT GPT-6. Applies ONLY to the independent repository `pddkalyan/ai-movie-studio-excelnt`.*

## Verified from the owner's Excelnt dashboard

- Gateway **base**: `https://excelnt.ai/v1`. Authentication pattern: `Authorization: Bearer <KEY>`. Excelnt suggests `EXCELNT_API_KEY`, while our two-worker adapter uses **separate private** environment slots.
- Keys are issued inside the signed-in **Excelnt VS Code extension**, shown once, and appear in the dashboard API Keys page. The user-supplied dashboard showed `0/25` keys on one account at the time of observation. Nothing establishes the second account's current key count.
- Power includes $600 five-hour and $4,200 weekly nominal usage allowances. **A separate existing $600 balance may be charged for API usage once included allowances run out**, per billing documentation. Zero top-ups does NOT mean no balance usage.

## Current code and what is deliberately blocked

- A = `EXCELNT_WORKER_A_API_KEY`. B = `EXCELNT_WORKER_B_API_KEY`.
- `python -m scripts.excelnt_readiness` checks only *presence* of non-placeholder private key material and displays Boolean-only sanitized statuses; it makes **zero HTTP/model requests**, never prints the keys, and will not authenticate them remotely.
- The gateway origin is strictly allowed only at the documented base URL; no unverified `/models`, `/chat/completions`, `/responses` or provider-specific paths are assumed.
- `studio/excelnt_accounts.py` **blocks all model requests and automatic key rotation**, even when both keys are present; it cannot start workers A/B or consume quota.
- A private key does not prove it belongs to a *different* account. Only an official authenticated account-identity API (or user-confirmed independently verified provider binding) can establish that.
- No key is stored as a GitHub secret, file, or chat message; no credentials are available to the CI runner.

## Required owner/provider checks before creating any credential

1. Ask Excelnt support/docs for exact **official** model routes and request schema, available model IDs, signed-in accounts' independent-use terms, and an authenticated read-only source for **five-hour/weekly remaining quota and reset timestamps**. The provided gateway base URL alone is insufficient.
2. Obtain a **provider-enforced** setting that prevents any API key on either account from debiting the separately available $600 balance after included allowance expires. Also prevent paid overage, auto-topup and unwanted plan renewal. A client-side percentage warning is defense-in-depth, **not** a server-side spending ceiling. If no such setting exists, unattended Excelnt workers remain DISABLED.
3. Verify the extension's package publisher, version, vendor-provided SHA-256 checksum and scope before installing it. Prefer **VS Code Extensions → Install from VSIX** in an isolated, trusted VS Code profile. Do NOT run `irm excelnt.ai/install.ps1 | iex` or install unknown scripts directly.
4. Only after all the above and explicit approval: create **one** key in Account A's private signed-in extension, store it in a private secrets manager under `EXCELNT_WORKER_A_API_KEY`, and check sanitized readiness locally. This is NOT a live auth test; do not post the key or a screenshot containing it. Then independently onboard B if allowed by provider terms.
5. For remote execution, store keys under worker-scoped protected secret storage only **after** the live adapter is independently reviewed. No public PR/Issue should contain key values, token fingerprints, account IDs, private session data, budget balances or user emails.
6. Once an official route, full authenticated quota/identity endpoint, and server-enforced spend lock are proven, add a separate **reviewed** live adapter with durable pre-send request ID, 80% warning/90% stop, explicit account isolation, no automatic account rollover and provider-confirmed reset/resume; test its mock adapter first. Any unknown, stale, 401/403, 429, timeout, crash, missing receipts or depleted allowance blocks and checkpoints instead of retrying paid usage.

## Legitimate credential replacement

To replace a key **on the same authorized account**: pause that worker, checkpoint and reconcile outstanding requests, revoke the old key in Excelnt, create a new key under that account using the provider-supported flow, update ONLY that worker's private secret, then verify safe-mode readiness and later the authenticated binding. The other worker must remain unaffected. Replacing a key does not refresh that account's five-hour usage; new accounts must not be created or cycled to circumvent promotional or rate restrictions.

## Implementation status and security report

- `studio/excelnt_accounts.py` — offline A/B separation, strict gateway base, sanitized readiness, safe key replacement policy, model send disabled.
- `scripts/excelnt_readiness.py` — read-only offline self-check.
- `tests/test_excelnt_accounts.py` — synthetic-key and failure-path tests, no paid API usage.
- Phase 0 workflow automatically runs all offline tests on Ubuntu and Windows Python 3.11/3.12 when this candidate PR targets `develop`.
- Original Movie Studio/Jules/Antigravity repository is independent and untouched.

**Current status: A/B adapter scaffold ready for review. Excelnt account connection, model identity verification, vendor cap, real inference and ongoing automated workers are NOT ACTIVATED.**
