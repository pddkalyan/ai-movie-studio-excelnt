# Excelnt API metadata evidence (EX-0005)

Source: user-provided authenticated Excelnt API Keys dashboard text dated 2026-10-11. The account itself and keys are NOT available to this repository.

| Item | Verified from supplied page | Limitations |
| --- | --- | --- |
| Gateway base URL | https://excelnt.ai/v1 | Base URL only; per-operation routes and request/response schemas not documented here |
| Authentication | Authorization: Bearer <secret key> or environment EXCELNT_API_KEY | Never paste, commit, log, or disclose the key; use approved private environment/secret store only |
| Issuance | Key created in signed-in Excelnt VS Code extension; shown once | No provider key can be generated from GitHub source code without authorized signed-in extension |
| Account provision | 0/25 active keys shown at observation | This is a screenshot/text snapshot, NOT live telemetry or account access |
| Traffic | 0 requests today shown at observation | Not evidence of current quota after that observation |
| Provider capabilities | Editor documentation names a GPT 6 Astra model | Label alone does not establish genuine upstream OpenAI routing, pricing, or supported API method |

Unverified: GET /models, POST /chat/completions, POST /responses, official usage/billing endpoints, request limits, token accounting, model IDs, server-side hard plan-only spending restriction, automatic renewal and two-account concurrency terms. Do NOT assume endpoint routes, test credentials by guessing, or make an inference call based solely on the gateway root.

**Critical billing:** the owner-provided Power Billing screen states that the separate $600 available account balance funds API usage once the included $600/5-hour plan allowance runs out. It is distinct from $4,200 weekly included usage. Zero top-ups does not block spending that separate existing balance.

Before activation, obtain written/provider-documented evidence of a hard account/API-key configuration that prevents ANY deduction from separate balance, top-ups, paid overages or unwanted renewals. Local client-side 80/90% threshold is not provider-enforced protection. Without that server control, STOP and keep the workers offline.

Only after provider docs, terms, secure extension package publisher/version/checksum and owner consent are verified: create one key locally in isolated VS Code profile, store it outside this public repository, verify genuine usage reporting and hard caps, approve a minimal included-allowance test on one account, then consider independent worker B. Do not post any key, email address, account cookie, or private balance event to GitHub.
