# AI Movie Studio — Excelnt Edition

Independent cloud-first cinematic-production research, completely separate from pddkalyan/project-agent-orchestrator. Nothing in that older repository is modified.

## Product goal

Produce real, auditable **20-minute (1,200-second), 16:9 cinematic episodes** with a consistent Movie Bible, named characters and voices, image/video reference control, screenplay -> scene -> shot planning, T2V/I2V/V2V and motion control, multi-character lip sync, dialogue, SFX, an exactly aligned timeline, visual/audio QC, and verified Google Drive archive. Provider interfaces must be replaceable and no additional spend is authorized.

## Phase 0: offline structure, NOT a movie

The current candidate provides Python standard-library contracts for exactly 1,200 seconds at 1920x1080, 24 fps. A deterministic demonstration maps 12 scenes to 120 ten-second shots (28,800 planned frames) with strict no-gaps, character/voice/reference association and zero generated clips. It is **not actual video**.

Other code: disabled-by-default generation provider contract, independent worker A/B quota contracts requiring provider-confirmed no-paid-balance fallback, atomic task checkpoints, and Linux/Windows offline CI. Excelnt is **not connected**. Neither worker is active.

Run without API accounts or cost:

    python -m unittest discover -s tests -v
    python -m scripts.offline_demo

The printed demonstration explicitly identifies itself as plan_only=true, rendered_clips=0, archive_uploaded=false.

## Planned worker ownership

- Worker A: studio/story, tests/story and docs/story — Movie Bible, character voice/reference consistency, screenplay and shot planning.
- Worker B: studio/media, tests/media and docs/media — provider-neutral video/audio, lip sync, SFX, timeline, QC and archive integration.
- Coordinator: frozen shared contracts, security, quota and CI. Workers must never write each other's files or reuse another user's credits to bypass provider limits. Separate clean branches/worktrees and draft PRs. No auto-merge or Phase3.

## Critical Excelnt billing facts

The owner-supplied Power plan shows **$600 included per five-hour window**, **$4,200 weekly allowance**, and a **separate $600 balance available for API usage**. Excelnt states: **Balance funds API usage once the plan allowance runs out.** Thus zero top-ups DOES NOT mean the existing balance cannot be debited. Power plan price shown is $240/30 days and automatic renewal settings were not verified. Our guards fail closed until provider-enforced balance fallback, paid overages and auto-topups are independently proven OFF. A screenshot is not an official usage API. Excelnt's editor extension does not by itself prove cloud API or upstream model routing.

See docs/EXCELNT_GATE.md, docs/ACCEPTANCE.md, docs/WORKERS.md and AGENTS.md.

## Git branching and provider gateway

The tested Phase 0 code is now on the **develop** integration branch; the **main** default/release branch is deliberately unchanged. All new Worker A/Worker B branches must originate at develop, submit feature PRs **targeting develop**, then receive tests and approval. Actual releases require a separate, reviewed **develop -> main** PR. See docs/BRANCHING.md.

The owner-provided Excelnt API Keys dashboard documents gateway root **https://excelnt.ai/v1** with **Bearer** authentication and key issuance through the VS Code extension (currently **0/25 active keys** at the supplied observation). It does not document the exact model request endpoints or a secure quota API. No key has been created or connected. See docs/EXCELNT_API_EVIDENCE.md.

## Public repository and evidence

Never commit Excelnt keys, email addresses, secrets, prompts with private data, movie voice/image sources, account statements, browser cookies, rendered output or unapproved logs. No automatic subscription/paid provider call, no pipe-to-shell downloads. Offline CI needs only read permission. Final movie success requires actual checksum-verified media, sound, lip sync, 20-minute runtime and archive — green planning tests do not demonstrate that.
