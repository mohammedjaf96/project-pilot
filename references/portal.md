# Local portal and state commands

Python 3 standard library only. One persistent HTML page, loopback-only authenticated HTTP, no AI calls, telemetry, CDN, or package installation. The portal is a supporting tool, not the product. It opens in the default browser.

## Start once

Use absolute paths; placeholders below must be replaced. State normally lives at `<project>/.projectPilot/state.json`; choose one coordination root for multiple repositories.

```sh
python3 <skill>/scripts/portal.py init --state <project>/.projectPilot/state.json
python3 <skill>/scripts/portal.py serve --state <project>/.projectPilot/state.json
```

Run `serve` through the host's long-running process facility without blocking the turn. It binds to `127.0.0.1` on an automatic port; `--port` is optional. Restarting preserves state. `--no-open` stores the private launch URL at `.projectPilot/.local/launchUrl`; open it locally without printing/publishing its token.

Exclude `.projectPilot/.local/`, `.projectPilot/.pilot.lock`, and `.projectPilot/.pilot-*` using the existing ignore mechanism before committing clean state. Keep temporary patches, logs, personal data, and secrets out of Git and shared state. The private URL is not a remote-sharing link.

## Read the smallest useful view

```sh
python3 <skill>/scripts/portal.py brief --state <state.json>
python3 <skill>/scripts/portal.py ready --state <state.json> --limit 5
python3 <skill>/scripts/portal.py show --state <state.json> --feature orders
python3 <skill>/scripts/portal.py show --state <state.json> --section answers
```

`brief` emits compact JSON: revision, baseline digest, two progress counts, handoff, bounded due queues/blockers, final status, and Plan 2 approval flag. `--limit` bounds queue/blocker counts, not the length of author-written handoff text. Omitted counts are explicit; use a larger limit or a section read for complete details. `show --feature` preserves the complete acceptance contract, children, direct edges, and dependency progress. `--section progress --feature ID` reads just that progress entry. Full `show` remains available for repair/export, not routine resume.

`ready` returns pending Track 1 IDs and eligible Track 2 IDs. It returns no work before adoption. Track 1 candidates are not proof that a feature is implemented or unblocked; inspect its contract and recorded next action. Read complete answers on first adoption or when a recorded decision is relevant, not every turn.

## Update without resending the project

```sh
python3 <skill>/scripts/portal.py update --state <state.json> --feature orders --revision 4 --input <progress-patch.json>
python3 <skill>/scripts/portal.py update --state <state.json> --revision 5 --input <state-patch.json>
```

Feature mode patches only one selected primary feature's progress. Supplied `track1`/`track2` fields merge one level into that track; other supplied feature fields replace their value. Omitted features/tracks remain unchanged. General mode replaces supplied top-level fields, never recursively merges them. Successful updates return the new revision. Reuse that revision until another writer changes it; on conflict, read only affected latest fields and merge deliberately.

A process/file lock and atomic replacement protect CLI/HTTP transactions. Do not edit JSON directly while serving. Baseline, answers, revision, schema version, timestamps, draft, and approval are runtime-owned. After adoption, proposal/questions are immutable. One agent owns state updates; workers return findings.

## Decisions and live progress

Read [State schema](state-schema.md) when preparing fields. Fill proposal/questions/defaults, then mark `readyForAdoption`. Explicit submission snapshots the baseline; later changes belong in Plan 2. Custom answers may need interpretation, never a rewritten snapshot.

The browser polls every two seconds and renders changed revisions; unchanged polls return no state body. Browser polling makes no model calls and is not itself a token-saving mechanism. Drafts persist locally; adoption and later Plan 2 approval are explicit. Buttons do not launch agents. If the host cannot wait/resume automatically, ask the user to notify it after submission.

Never expose the server beyond loopback or disable authentication to share it. A remote portal needs separate authorized deployment and access control. Runtime messages can be explained in the user's language; portal labels/content are localized through state, while this repository stays English.
