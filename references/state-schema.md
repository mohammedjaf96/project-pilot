# State schema (load only when authoring fields)

`init` creates schema version 1. Existing version-1 state remains compatible; the new views are read-only projections, not replacement state. Do not put full code, chat history, large logs, or credentials in it.

| Field | Contract |
|---|---|
| `language`, `direction`, `title`, `labels` | User-facing locale, `ltr`/`rtl`, title, and translated UI strings. All authored portal content follows the user's language; source examples remain English. |
| `proposal` | `idea`, concise `decisions`, `features`, and `edges`. |
| Feature | Stable `id`, `title`, `kind` (`primary`/`secondary`), `parent` for a secondary's primary owner, and `acceptance` operation strings. Optional owned paths and contract pointers may be included. |
| Edge | `from`, `to`, `reason`, `operations`. From depends on to. Child endpoints resolve to their primary owners. Direct meaningful integrations only. |
| `questions` | `id`, `title`, `description`, `options` with `value`/`label`/optional `description`, `default`, and `recommendation`. Custom text is supported; blank uses default at adoption. |
| `readyForAdoption` | Enable only for a complete usable proposal with primary acceptance and visible defaults. |
| `baseline` | Runtime-frozen proposal, questions, resolved answers, selected primary IDs, and adoption time. Selected scope must include declared prerequisites. |
| `progress` | Map keyed by primary ID: `status` (`pending`/`inProgress`/`blocked`), `track1`, `track2`, evidence and input identities, `nextCheck`. Each track has `status` (`pending`/`passed`/`failed`) and actual evidence pointers. Runtime prerequisite validation is not test execution. |
| `handoff` | Concise `lastAction`, concrete `nextAction`, optional current feature, owned paths, changed paths, relevant rule pointers. Reference long notes rather than repeating them. |
| `blockers` | Concise strings or objects with `description` and evidence. Keep resolved history outside the active blocker list. |
| `finalChecks` | `status` (`pending`/`running`/`failed`/`passed`), localized `summary`, commands/results/input identities. Passed requires all adopted tracks and actual final suites/builds. |
| `plan2` | Entries with `id`, `title`, `description`, `impact`, affected `features`, one/two `options`, optional editable `proposal`. |
| `plan2Approval` | User-owned snapshot of selected item IDs/edited proposals and approval time, available after final verification. Start a separate cycle for follow-up execution if needed. |
| `delivery` | Safe run instructions, repository/commit references, deployment state, and external requirements. Values render as text, never untrusted HTML. |

`revision`, `updatedAt`, `answers`, `baseline`, `userDraft`, `schemaVersion`, and `plan2Approval` are runtime-owned. General patches cannot overwrite them. Progress evidence may be recorded at feature/track level; keep the path set and context needed to check validity.

## Example feature-progress patch

```json
{
  "status": "inProgress",
  "track1": {
    "status": "passed",
    "changeIdentity": "sha256:<input-digest>",
    "command": "python3 -m unittest tests.test_orders",
    "evidence": [".projectPilot/evidence/orders-local.txt"]
  },
  "nextCheck": "Track 2 after products and payments pass Track 1"
}
```

Use this as a feature-mode patch only after the check actually passed; placeholder IDs/digests are documentation, not evidence. Reset affected passes to pending when their inputs change and reset final checks accordingly. For multi-feature invalidation, merge the latest progress map once rather than issuing stale patches.

## UI labels

Supply every key for a fully localized portal; English is the fallback:

`progress`, `track1`, `track2`, `final`, `idea`, `graph`, `features`, `questions`, `scope`, `all`, `selected`, `adopt`, `adopted`, `defaults`, `handoff`, `plan2`, `plan2Hint`, `approvePlan2`, `delivery`, `connected`, `disconnected`, `updated`, `pending`, `inProgress`, `blocked`, `track1Passed`, `bothPassed`, `recommendation`, `custom`, `blank`, `saved`, `conflict`, `error`, `empty`, `lastAction`, `nextAction`, `approvedPlan2`, `saving`.
