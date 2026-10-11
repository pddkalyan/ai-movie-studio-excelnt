# Branch strategy — Excelnt Edition (EX-0005)

Established 2026-10-11 by GPT-6, for the independent repository pddkalyan/ai-movie-studio-excelnt.

## Long-lived branches

| Branch | Purpose | Changes allowed |
| --- | --- | --- |
| main | Stable release snapshots (GitHub default branch) | Explicitly approved release PRs from develop only |
| develop | Tested integration of independently reviewed worker changes | Approved, passing feature PRs; no direct unreviewed changes |

main remains unchanged at initial commit f245ac9de8cffeb5e269493808ec61ff30de173c. 
develop was created from Phase 0 draft PR #1 exact tested head b20b3c068377fc04eda8140c634748ba1e0c2ebf.
PR #1 is a preserved initial review packet targeting main, not an automatic release. Once develop advances, create a NEW accurate develop -> main release PR for the desired release SHA; never treat the old frozen PR #1 as containing newer changes.

## Regular flow

1. Start independent A/B worker or coordinator feature branch from the CURRENT develop SHA.
2. Keep a unique task claim; each worker edits only its owned paths. No shared worktrees, no destructive reset/stash/clean or force push.
3. Run deterministic offline tests locally and in GitHub Actions, with exact commit SHA. Leave external Excelnt model calls DISABLED.
4. Open a draft feature PR with base develop; request independent code/security review. Apply concrete corrections, rerun all affected CI jobs. Do not auto-merge.
5. After explicit owner-approved integration, merge tested work into develop via reviewable PR. Never bypass branch gates even for documentation.
6. Promote develop to main only through a separate develop -> main release PR, pass complete regression and security/zero-spend gates, obtain explicit release approval and review exact final SHA.
7. main remains default for release and GitHub entry point; do not change default branch just to route developer PRs. Always explicitly choose develop as the PR base.

## Enforcement status and GitHub settings

The branch rules above are project policy. They are NOT evidence of GitHub-native branch protection being enabled.
Owner should use repository Settings > Rules > Rulesets (or Branches > Add branch protection rule) to require pull requests on both main and develop, restrict force pushes/deletion and require appropriate passing CI/reviews. Do not assert such a ruleset exists until GitHub confirms it.
The read-only offline CI listens on pushes to main/develop and PRs targeting main/develop. Workflow credentials only have contents: read.
No automated merges, paid calls, account cycling, direct release pushes, or inference/secret exposure.
