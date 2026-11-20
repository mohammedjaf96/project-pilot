# Execution and compact context

## Feature-sized work

Implement database/backend/client/dashboard parts and subordinate operations of one primary feature together, in dependency order. Establish only the common foundation needed next. Preserve data and compatibility. Include appropriate authorization, input boundaries, secret protection, resource bounds, and performance; do not defer required protection or add speculative hardening.

## Reuse instead of rediscovery

1. Read `brief` for revision, baseline digest, progress, due checks, blockers, and handoff.
2. Read `show --feature ID` for the current contract and direct dependency evidence. Read adopted answers or another section only when that task actually needs it.
3. Inspect recorded owned files and relevant diffs. Search outside them only for a specific unresolved symbol, dependency, or failure.
4. Checkpoint the result and one concrete next action after a feature, decision, meaningful failure, or handoff. Do not narrate every tool call into state.

A handoff carries only feature ID, acceptance, stack/rule pointers, owned paths, direct contracts, tested inputs, evidence locations, defects/blockers, and next action. Keep full logs/code outside state. Store long notes separately and reference the relevant section. Completed feature details remain retrievable; do not put all of them in every resume summary.

## Evidence identity

Record each check's command, relevant source/config/test paths, dependency contract identities, runtime/toolchain context, result, and artifact pointers. Use `scripts/fingerprint.py` to hash the declared inputs without scanning the repository. A matching digest supports reuse only if the declared input set is complete and the environment/external data assumptions still hold; it is not proof of a passing test.

```sh
python3 <skill>/scripts/fingerprint.py --root <project> --files src/orders.py tests/test_orders.py pyproject.toml --command "python3 -m unittest tests.test_orders" --context "python=3.13" --context "products-contract=v2"
```

The command string is hashed, never executed. Include all relevant configuration, tests, and dependency identities; a missing input fails rather than silently disappearing. Record the input list with evidence. No secrets belong in command text or context.

Unrelated edits and commit/push alone do not invalidate evidence. Changed implementation, meaningful conflict resolution, relevant test/config/dependency changes, or changed environment assumptions invalidate affected checks. Record the reason and reset affected track results and final checks before reporting new progress. Include reverse consumers when their named operations are affected; do not clear unrelated passes or assume every transitive feature must rerun.

## Delegation

Use independent complete features only when coordination saves work and the host permits agents. Agree shared contracts and file ownership first; use isolated branches/worktrees when needed. One coordinator owns integration and state writes. Do not fork the full conversation when a compact packet suffices.

A scoped checker diagnoses the due track without editing implementation. Call a different fixer only for reproduced defects, then recheck failed cases and direct effects. If independent agents are unavailable or disproportionate, do these roles sequentially and describe the review accurately. Another independent feature may proceed without invalidating the tested inputs.

## Retry and scope discipline

For one approach, cap attempts at three if each lasts at most five minutes, otherwise two; discovering a longer attempt never authorizes another. Every retry must change a hypothesis/input and record what was learned. After exhaustion, allow at most two distinct alternative approaches with the same cap. Then record the blocker, continue independent work, and ask a targeted question. Never bypass permissions or remove required behavior to pass.

New scenarios and later requested changes go to Plan 2 with impact, affected IDs, and one or two options. Failures of adopted operations remain baseline defects. Present Plan 2 after final baseline verification; user edits and explicit execution approval start a separate cycle without rewriting baseline accounting.
