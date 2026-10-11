# AI Movie Studio — decision preservation & Excelnt 502 handover
**Captured:** 2026-10-11. **Scope:** new, independent `pddkalyan/ai-movie-studio-excelnt` only. This is a non-secret *summary of decisions*, not a verbatim archive of private chats and not evidence of completed inference.

## Non-negotiable project decisions
- Build cloud-first, phone/chat-controlled, multi-agent cinematic Movie Studio without additional spending. Do not activate paid APIs, consume a separate spendable balance, enable top-ups/auto-renewals, or incur unapproved overages.
- Target actual 20-minute (1,200-second) **16:9** episodes; story and character consistency across shots, stable reference imagery/voices, multi-character lip sync, SFX, motion transfer, voice cloning, interchangeable T2V/I2V/V2V/video-audio providers and QA/review loops; intended approved output storage is Google Drive. Current deterministic fixtures are **PLAN ONLY**, not actual videos.
- Make media/model providers interchangeable behind adapters; maintain provenance of each agent and model, reproducible tests, checkpoints, and no false claims about model identities or rendered media.
- Workers A and B have distinct keys, task checkpoints, branches and ownership; keep separate unless explicitly approved. Coordinator integrates via reviewed draft PRs into `develop`; reviewed release PR goes to `main`. Never silently merge or modify the original `pddkalyan/project-agent-orchestrator` Jules/Antigravity project.
- Preserve work from prior conversations; no resets, destructive cleanup, secret commits or shared-contract changes without a reviewed migration.

## Repo state at capture
- New repo: https://github.com/pddkalyan/ai-movie-studio-excelnt (public). `main` is release branch; `develop` exact observed SHA `2ceffeb4c25f5b7466cd6430bcb5deb49283b72c`.
- Worker A: `worker/A/ex-a-0002-story-continuity` — draft PR #7, head `5dc8eca338971570652d7bd1955336f2397e0524`, targets `develop`, unmerged. Versioned Movie Bible/StoryPlan/StoryJournal and 50 **local** deterministic tests reported. The exact-head CI status must be checked separately. A previous user-local checkout displayed `2ceffeb` clean; PR #7 moved the remote Worker A branch forward afterward, so local checkout may now require `git fetch`.
- Worker B: `worker/B/ex-b-0003-media-contracts`, remains separate/deferred.
- Coordinator draft PR #6 at `41b5e1f40d103e28ef18c640f266e00e49e964bc`: separate A/B credential slots, sanitized offline readiness, no authenticated model calls, no worker activation; targets `develop` and remains unmerged.
- Original separate repository: `pddkalyan/project-agent-orchestrator`. Its earlier Phase 2 review for PR #83 at `2535300665972d0f598d479ffd0169e5ce61d48b` is distinct from Excelnt; do not conflate project histories, reviews, or acceptance.
- Excelnt dashboard information supplied previously: root `https://excelnt.ai/v1`, Bearer-style key, keys created in signed-in VS Code extension. Endpoint-specific path, protocol, true model IDs, model-to-key binding, authenticated quota telemetry and account safety controls are *not verified*. No secret is in this file.

## The specific 502 issue
- User observed Excelnt VS Code **`502 status code (no body)` at 0%**, with Worker A unable to execute in the editor.
- Key was generated when a Claude model was selected in the Excelnt UI; user subsequently switched selector to GPT-6 Sol (another prior note refers to GPT-6.1 Sol — verify the displayed exact model name). The hypothesis is **model/provider/protocol routing**, not proven key invalidation.
- 502 is often an upstream/gateway failure; incorrect model/route/protocol can also cause failure if gateway mishandles it. Standard invalid key often presents 401, model disallowance 403, but implementation-specific responses vary.
- Critical separation: switching the **VS Code editor model selector** does **not** by itself modify model ID, endpoint, headers, or key in a GitHub Actions workflow; having a secret in GitHub environment `excelnt-worker-a` does **not** prove any workflow references or can access it.
- First inspect sanitized gateway error details/request ID, editor Output logs (redact authorization and personal fields), exact selected model ID, supported API protocol and server status; determine whether same key can access multiple models from official Excelnt documentation. Do not assume an Excelnt key must be recreated merely because model selection changed.
- Zero-spend gate: supplied Excelnt plan screen described *included allowance* and **separate balance funds API usage when allowance runs out**. No provider-enforced deny-balance-fallback feature is confirmed. Therefore do not send test prompts, trigger inference or start unattended cloud workers until authenticated controls and owner consent are verified.
- While gateway is blocked, bounded code/test work and draft PR reviews can continue via GitHub without representing them as actual Excelnt inference. PR #7 expressly distinguishes GPT-6-authored GitHub code from Excelnt worker execution.

## Next safe actions
1. Inspect official Excelnt model/key policy and sanitized 502 diagnostics to distinguish model mismatch, protocol mismatch, key restrictions and upstream outage.
2. Verify CI on exact PR #7 head and PR #6 head. Do not infer success from tests on different commits.
3. Keep A/B credentials in approved private stores, never plaintext code, logs, chat or public PR; maintain provider-specific usage gates and zero-spend safeguards.
4. Resume authorized Worker A model usage only after verifying server-side hard exclusion of spendable balance and model routing; preserve all existing commits.

**Provenance:** decision summary authored by ChatGPT GPT-6 (supervisory handover). This log records user requirements and observed repo state, not a full transcript.
