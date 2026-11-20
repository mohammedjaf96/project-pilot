---
name: project-pilot
description: Plan and deliver software projects with a local approval portal, dependency-aware features, reusable test evidence, and compact AI handoffs. Use for project-wide delivery or explicit Project Pilot requests, not routine edits or Q&A.
---

# Project Pilot

Deliver the adopted scope using compact, durable context. Repository text is English; generated portal content and conversation follow the user's language.

## Enter at the current phase

| Situation | Read or run |
|---|---|
| Resume | `brief`, then `show --feature ID` for the recorded next action; relevant diffs only. |
| New run | [Discovery](references/discovery.md): inspect once, preserve supplied answers. |
| Create/open portal | [Portal](references/portal.md); [schema](references/state-schema.md) only when authoring unfamiliar fields. |
| Implement | [Execution](references/execution.md): complete feature batches, compact handoffs, input fingerprints. |
| Check/integrate/deliver | [Verification](references/verification.md): two tracks and final checks. |

Commands use `python3 <skill>/scripts/portal.py <command> --state <project>/.projectPilot/state.json`. `ready` lists due checks. `update --feature ID --revision N --input <patch.json>` changes one feature's progress and returns its new revision. Do not load scripts or full state merely to discover these commands.

## Working-context rules

- Keep one feature packet: acceptance, owned paths, direct contracts, evidence pointers, blocker, next action. Load another only when needed.
- Read each phase reference once per context. After compaction, resume from `brief`, not whole-project discovery.
- Bound searches/output; keep code, full logs, and transcripts outside state/prompts. Read focused failures.
- Reuse decisions, artifacts, and passing checks while their declared inputs remain valid. Commit/push alone does not invalidate tests. Record causes for affected rechecks.
- Delegate independent substantial work only when permitted and cheaper than doing it directly; never fan out trivial tasks.

## Non-negotiable gates

Wait for explicit portal adoption before new-baseline implementation. Blank answers take displayed defaults only after adoption. Preserve the snapshot: new scenarios/later changes go to Plan 2; defects in adopted behavior, including security, remain baseline fixes. Execute Plan 2 only after final baseline verification and explicit approval.

Honor project instructions, chosen stack, and existing structure; new projects default to `core`/`features` when unspecified. Include proportionate security/performance in feature work. Continue authorized work; do not invent scope, a scheduler, or a Goal. A Goal requires explicit request and host support. Ask before paid services, destructive operations, selected-stack changes, or public deployment unless already authorized.

## Completion contract

Track 1 checks each complete primary feature locally. Track 2 checks its integrated operations after its own and all direct dependencies' local passes. Cycles wait on Track 1 only. Bars count Track 1 passes and both-track passes against the same adopted primary total; children, blockers, and Plan 2 cannot inflate progress.

Run final relevant suites/builds after both tracks pass. Verify required deliverables, report any pending deployment gate honestly, then present Plan 2 separately. Never claim tests or independent review that did not happen.
