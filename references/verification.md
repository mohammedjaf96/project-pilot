# Verification and delivery

## Track 1: local feature completion

Check every adopted operation and child of the completed primary feature, including real wiring, relevant coding rules, security, and performance. Run focused tests and directly affected checks. Record actual results against tested input identities and evidence paths. Reuse valid prior evidence for existing code; never claim a screen or a partial pass is a completed feature.

## Track 2: integration readiness

Use `ready` to avoid repeatedly recomputing prerequisites. Feature A becomes due only when A and all its direct primary dependencies have Track 1 passes. Check A's operations using those dependencies, not their entire test suites. Do not recheck A whenever just one dependency finishes. Cycles depend on local passes, not integrated passes. An unknown required operation or blocker is not a pass.

Recheck affected operations after relevant changes, preserving unaffected evidence. The CLI computes readiness from recorded statuses; it neither runs tests nor authenticates evidence. A displayed pass must still be backed by real checks.

## Final verification

After all adopted primary features pass both tracks, run the full relevant suites and required component builds. Fix failures and recheck failed cases/direct regression effects. Repeat a full suite only when new changes or unresolved evidence warrant it. Final verification does not restart discovery or authorize extra work. Keep final checks distinct from progress bars and pending deliverables.

## Git integration

Preserve the existing principal branch (`main` or `master`). For a feature that passed Track 1, stage only intended changes, commit/push a meaningful `feat/featureName` branch, merge with visible feature history where supported, and push the principal branch. Do not force-push, mix user changes, or bypass protection. Use an authorized PR path when direct integration is restricted. A missing remote requires a destination, not a fabricated push claim.

For multiple repositories, keep contract-compatible changes together and record each commit. Confirm evidence matches integrated inputs; merge conflict resolutions invalidate affected checks. Commit/push alone does not require retesting. The workflow supports routine feature integration, subject to the user's current scope and host permissions; it does not grant unrelated publication or data-deletion authority.

## Accounting and handover

Both denominators are adopted primary features. Track 1 counts valid local passes; Track 2 counts features with both passes. Children count through parent acceptance. Blockers stay included; Plan 2 stays separate. Invalidated evidence may reduce progress with an explained cause. Never count files, tokens, or test totals as feature progress.

The portal's delivery section records implemented scope, repository/commit links, run instructions, final results, deployment state, and concrete prerequisites. Prepare deployment artifacts before any required final approval; a general scope adoption is not public-deployment approval. Declare completion only when required checks and deliverables are verified. Then present Plan 2 for explicit execution approval.
