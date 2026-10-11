# Non-overlapping worker assignments

## Excelnt Worker A — NOT CONNECTED
Area: studio/story/, tests/story/, docs/story/.
Implement immutable/versioned character bible, screenplay->scene->shot decomposition, constraints preserving voice and visual references across edits. Candidate branch worker/A/<task> (separate task lease). No provider calls, no shared-contract edits without owner review.

## Excelnt Worker B — NOT CONNECTED
Area: studio/media/, tests/media/, docs/media/.
Implement replaceable cloud video/image/audio/lipsync interface contracts, clip integrity evidence, timeline checks, QC and Google Drive archive adapters. Separate branch worker/B/<task>. No real output claims, no provider calls or shared-contract edits without approval.

## Coordinator
Frozen studio/contracts.py, provider_contract.py, quota_contract.py, checkpoints.py, CI, provenance and review. Must verify source provenance, nonoverlapping branch ownership and actual tests. Hourly ChatGPT status monitoring is NOT an execution agent. All worker sessions are OFF until separately authenticated provider execution and zero-balance-use enforcement are verified.

Workers must checkpoint before interruption; do not replay an ambiguous model request; never rotate accounts to bypass Excelnt terms.

## Git branch base and PR targets

Each worker's feature branch MUST start from current develop. All independently scoped draft PRs target develop, not main. Final release is a separately owner-approved develop -> main PR. See docs/BRANCHING.md. Original Movie Studio repo is strictly out of scope.
