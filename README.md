# Project Pilot

**A context-efficient AI agent skill for taking software projects from an idea or existing codebase to approved scope, verified features, and a clear delivery handoff.**

Project Pilot gives Codex and Claude Code a durable project workflow: a local decision portal, dependency-aware feature batches, two-track verification, compact resume packets, and reusable test evidence. It reduces repeated repository discovery and oversized handoffs without treating fewer checks as proof of quality.

## Why Project Pilot

- **Resume without starting over.** Read one compact brief, then the current feature's acceptance and direct dependencies.
- **Approve scope once.** A local portal records decisions, custom answers, selected features, and an immutable adopted baseline.
- **Deliver complete features.** Keep database, backend, client, and dashboard operations together instead of shipping disconnected layers.
- **Verify when dependencies are ready.** Run feature-local checks first, then meaningful integration checks after all direct prerequisites pass locally.
- **Reuse valid evidence.** Fingerprint declared source, tests, configuration, commands, and environment context instead of invalidating tests for an unrelated commit.
- **Keep later ideas separate.** Plan 2 preserves new scenarios and requested changes until explicit follow-up approval.
- **Stay local.** The Python portal uses the standard library, binds to loopback, and makes no AI API calls or telemetry requests.

## Install

### Codex

```sh
git clone https://github.com/mohammedjaf96/project-pilot.git ~/.codex/skills/project-pilot
```

For a custom `CODEX_HOME`, use its `skills` directory instead. If a local copy already exists, back it up or update that checkout rather than cloning over it.

### Claude Code

```sh
git clone https://github.com/mohammedjaf96/project-pilot.git ~/.claude/skills/project-pilot
```

Claude Code supports filesystem skills in personal or project skill directories. See the [official Agent Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview). Keep supporting scripts, references, and assets alongside `SKILL.md`.

The workflow needs a host with filesystem and shell access, Python 3.10 or later, and a browser for the local portal. Python commands may use `python` instead of `python3` on Windows. Subagents, persistent Goals, and background continuation depend on the host; the skill does not create those capabilities.

## Use

In Codex:

```text
Use $project-pilot to analyze this existing application, prepare its local
approval portal, and deliver the adopted scope with focused verification.
```

In Claude Code, invoke the installed skill or ask for Project Pilot:

```text
Use Project Pilot to plan this software project, collect my decisions,
and implement the approved features in dependency order.
```

For a resumed run:

```text
Resume Project Pilot from .projectPilot/state.json. Read the compact brief
and continue the recorded next action without rediscovering the repository.
```

## The delivery model

1. Inspect the idea or relevant existing implementation and identify real gaps.
2. Collect consequential choices through one persistent local portal.
3. Explicitly adopt the baseline; unanswered fields take displayed defaults.
4. Implement complete primary features and their subordinate operations.
5. Pass Track 1 locally, then Track 2 once direct dependencies pass Track 1.
6. Run final relevant suites and builds, verify deliverables, and report pending gates.
7. Present Plan 2 for editing and explicit execution approval.

The portal displays separate progress bars for locally verified features and features that passed both tracks. Progress counts adopted primary features, not files, tokens, or test quantities. Final build/test status and deployment readiness remain separate.

## Context-efficient commands

Replace paths with your installed skill and project locations:

```sh
python3 scripts/portal.py brief --state /path/to/project/.projectPilot/state.json
python3 scripts/portal.py ready --state /path/to/project/.projectPilot/state.json
python3 scripts/portal.py show --state /path/to/project/.projectPilot/state.json --feature orders
python3 scripts/portal.py update --state /path/to/project/.projectPilot/state.json --feature orders --revision 4 --input /tmp/progress-patch.json
```

- `brief`: compact revision, baseline identity, progress counts, next action, due queues, blockers, and approval flags.
- `ready`: pending local checks and integration checks whose direct prerequisites are satisfied.
- `show --feature`: one complete feature contract, children, edges, and dependency evidence.
- `update --feature`: patch one feature's progress without resending every other feature; receive the new revision.
- `fingerprint.py`: hash explicitly declared verification inputs without a repository scan or executing the supplied command.

See [portal commands](references/portal.md), [execution and evidence](references/execution.md), and the [state schema](references/state-schema.md) for precise behavior.

## Reproducible context-size comparison

```sh
python3 scripts/benchmark_context.py
```

In the bundled synthetic project with 60 primary features and four acceptance operations per feature:

| Context read | Characters |
|---|---:|
| Full formatted state | 93,412 |
| Compact resume brief | 676 |
| One complete feature packet | 1,016 |
| Brief plus feature packet | 1,692 |

That is **98.19% less context text for this synthetic resume payload**, while retaining the selected feature's full acceptance criteria. This measures characters, not model tokens, API billing, or end-to-end project cost. Results depend on project state, handoff size, the model, and whether the agent follows the workflow. A full state read remains available when actually needed.

Additional savings come from phase-specific references, focused searches, bounded diagnostic output, small handoffs, and retaining passing test evidence while its complete input set remains valid. Fingerprints do not prove tests passed or automatically discover every dependency.

## Repository layout

```text
project-pilot/
|-- SKILL.md
|-- agents/openai.yaml
|-- references/
|   |-- discovery.md
|   |-- execution.md
|   |-- portal.md
|   |-- state-schema.md
|   `-- verification.md
|-- scripts/
|   |-- portal.py
|   |-- fingerprint.py
|   |-- benchmark_context.py
|   `-- check_english.py
|-- assets/portal.html
`-- tests/test_runtime.py
```

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_english.py
python3 scripts/benchmark_context.py
```

Behavioral tests cover adoption, immutable scope, user-owned fields, stale revisions, dependency readiness, cycles, feature-scoped updates, final verification gates, Plan 2 approval, authentication, unchanged polling, and input fingerprints. GitHub Actions runs checks on Linux, macOS, and Windows.

## Boundaries

Project Pilot is a workflow skill and local support tool, not an autonomous hosting service or unlimited task scheduler. It does not certify an implementation, execute tests merely by recording a pass, or publish a project without the user's authorization. Browser submission does not wake an idle agent unless the host supplies that behavior.

Repository documentation, examples, comments, names, descriptions, and commit messages are English. The generated decision portal can follow the user's language through runtime labels and content. Keep credentials, launch tokens, private project data, and full logs out of this public repository.
