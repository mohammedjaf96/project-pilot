# Discovery

## Inspect once

Read applicable project instructions and the relevant implementation, not the entire repository. Capture known answers and focused findings once. Reuse existing working behavior and valid evidence; investigate a wider area only for a named dependency or observed failure. Do not start implementation before adoption.

Identify user-visible primary responsibilities and their subordinate functions. Backend operations, entities, and relationships are useful signals, not requirements: authentication, offline workflows, and client-only computation can also be primary. Keep stable feature IDs and explicit data ownership.

## Ask only consequential questions

Put missing decisions in the portal with a short explanation, one or two options, a recommendation, and custom text. Do not re-ask answered questions or interview the user about routine implementation details.

Cover applicable product parts: app/site, dashboard, mobile, backend, database, hosting; chosen technology and architecture; business rules; languages/layouts/accessibility; backups/monitoring where required; deployment environments/domain; external prerequisites without secrets. Do not ask delivery/time-budget questions or whether security and performance matter.

Offer all scope or selected feature groups. Blank scope means the whole idea at explicit adoption, never a silently reduced MVP. Respect existing structure; new projects default to reusable `core` capabilities and isolated `features` when appropriate to the stack.

## Permission model

For dashboard products, treat tabs as permission resources with supported actions such as read/add/edit/delete/approve/export. Tab access includes read. Job titles are labels, not invented authorization roles. An action affecting Categories needs Categories permissions even when launched from Products; viewing Products still requires Products read. Enforce resource, object, and tenant boundaries on the backend and hide unauthorized controls in the UI. Permissions remain editable; record required ownership exceptions.

## Graph and acceptance

For every primary feature, record all required user operations, children, relevant routes/endpoints, validation, permissions, failures, and measurable performance criteria where warranted. Connect A to B only when named operations of A use B; record the reason and affected operations. Resolve secondary nodes to their primary owner for verification. Do not connect everything merely because it shares a library or expand direct edges into all-to-all tests.

For cycles, establish the minimal common foundation, finish every member's local track, then verify their integrated operations. Avoid Track 2 deadlocks. Selected scope must include its declared prerequisites; explain missing selections instead of silently adding them.

## Adoption

Prepare complete acceptance and graph data plus displayed defaults, then enable one localized adoption control. Submission freezes the proposal, questions, answers, selected primary IDs, and adoption time. Unsubmitted pages are not consent. Resolve ordinary technical details within adopted choices; clarify a genuine contradiction before dependent work. Later answer changes become Plan 2 entries, never baseline edits.
