# Excelnt account and provider integration gate — FAIL CLOSED

Evidence from owner-provided Excelnt docs: editor extension for VS Code/Cursor/Windsurf, dashboard user sign-in, selectable model text labeled GPT 6 Astra, shared account usage. The separately provided API Keys dashboard now confirms an API gateway BASE URL, https://excelnt.ai/v1, Bearer authentication, the EXCELNT_API_KEY environment name, and that keys are issued through the signed-in VS Code extension (0/25 active keys at observation). This does NOT verify model-specific routes, the request/response protocol, upstream model identity, a supported quota endpoint, or an authenticated key for this repository. Do not guess endpoints from other providers. See EXCELNT_API_EVIDENCE.md.

Owner-provided Billing & plan screen:
- Power: $600 included each 5 hours and $4,200 weekly allowance.
- Separate $600 account balance marked available for API use.
- Excelnt explicitly says "Balance funds API usage once the plan allowance runs out. Plans are paid from balance."
- Paid total $0, zero topups, active Power plan $240 for 30 days until 2026-11-10.
- Plan renewal behavior and disabling fallback not documented.

**Zero topups does not protect the existing $600 from deduction.** Two accounts with equal limits does not imply credit transferability or permission to endlessly cycle through promotional signups.

Live use is BLOCKED until verified: official documented API/extension execution hooks; authenticated, recent, per-account five-hour and weekly usage observations; permitted multi-account terms; per-request worst-case usage caps; provider-enforced controls disabling all deduction from prepaid account balance, automatic paid overages, topups and plan renewals; verified extension publisher/version/checksum; and separate owner approval for a tiny included-allowance test. Provider may lack a no-balance-fallback feature; if so DO NOT run unattended.

Never store credentials, balance screenshots, billing IDs, private user metadata or cookies in the public repo. No real requests or account access in this Phase 0 code.

## EX-0006 — A/B connection slots prepared, still offline

The candidate `studio/excelnt_accounts.py` module binds A to `EXCELNT_WORKER_A_API_KEY`, B to `EXCELNT_WORKER_B_API_KEY`, rejects one identical secret in both slots, checks the documented gateway BASE `https://excelnt.ai/v1`, reports sanitized `credential_present` flags and **unconditionally rejects live model requests**. No provider keys have been created, downloaded, issued, or installed by this code; keys must remain in the owner's private secret storage and must never appear in public GitHub.

A credential being present is NOT evidence of separate account identity, a valid model route, sufficient included quota, genuine model provenance or provider-enforced prepaid balance protection. User must first verify those missing vendor facts and provide independent consent for a bounded included-quota request. See `docs/EXCELNT_AB_INTEGRATION.md` for safe onboarding steps. Key *replacement within the same permitted account* is supported by updating the private slot while paused; swapping to other accounts to evade quotas, promotions or multi-account restrictions is not allowed.
