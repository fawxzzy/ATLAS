# GitHub Control-Plane Event Admission Runtime - 2026-07-13

## Result

Atlas now owns the first deterministic admission compiler for canonical GitHub event receipts:

```text
_stack immutable normalized GitHub facts
-> atlas.github.event-receipt.v1
-> Atlas deterministic admission and deduplication
-> atlas.github.event-admission.v1
-> zero or more formatting-free atlas.github.projection-intent.v1 records
-> DiscordOS later dry-run and single-writer consumption
```

No backend was selected. No scheduler, queue, webhook, worker loop, Discord mutation, GitHub mutation, Vercel mutation, or Supabase mutation was implemented.

## Ownership

- `_stack` remains the only immutable GitHub fact producer.
- Atlas owns schema validation through `@atlas/contracts`, admission, deduplication, quarantine semantics, durable meaning, and projection-intent production.
- DiscordOS remains the only future external writer and is not called by this runtime.

## Compiler Surface

Module:

- `ops/atlas/github_event_admission.mjs`
- `compileGithubEventAdmission({ receipt, priorAdmissions, policy })`
- `loadPolicy(policyPath?)`
- `selfCheckGithubEventAdmission({ policyPath? })`

CLI:

```powershell
node ops/atlas/github_event_admission.mjs --receipt <canonical receipt JSON>
node ops/atlas/github_event_admission.mjs --receipt <canonical receipt JSON> --prior-admission <admission JSON>
node ops/atlas/github_event_admission.mjs --receipt <canonical receipt JSON> --policy docs/registry/GITHUB-EVENT-ADMISSION-POLICY.v1.json
node ops/atlas/github_event_admission.mjs --receipt <canonical receipt JSON> --output-dir tmp/github-event-admission
node ops/atlas/github_event_admission.mjs --self-check
```

CLI result rules:

- stdout always emits deterministic JSON with stable key ordering.
- `--output-dir` writes exact schema-valid artifacts by derived `gha_*.json` and `ghp_*.json` file names without choosing a ledger backend.
- `--self-check` validates the canonical policy plus the registered Atlas Contracts schemas used by the runtime.

## Deterministic Semantics

- Schemas resolve only through the Atlas Contracts validator registry.
- `observed_at` from the source receipt is reused as both `admitted_at` and projection `created_at`.
- `gha_`, `ghak_`, `ghp_`, and `ghpk_` identifiers are derived from SHA-256 over canonical sorted JSON inputs.
- Source `event_id`, source `idempotency_key`, digest, `event_family`, and `fact_state` are preserved exactly in downstream artifacts.
- Replaying the same receipt, prior evidence, and policy produces byte-stable stdout and artifact bytes.

## Admission Behavior

- First-seen schema-valid events are evaluated against the policy table.
- Same source `idempotency_key` plus same digest is classified as `duplicate` with `noop_duplicate` and no new projection intents.
- Same source `idempotency_key` plus different digest is classified as `quarantined` with `quarantine_hold` and stable digest-conflict reasoning.
- `conflicting` source fact state is quarantined fail-closed by policy.
- Malformed JSON, schema-invalid artifacts, invalid policy documents, and contradictory prior-admission evidence fail closed with stable machine codes and no secret echo.

## Policy Table

Canonical policy file:

- `docs/registry/GITHUB-EVENT-ADMISSION-POLICY.v1.json`

Policy guarantees:

- Every event family and every fact state has an explicit result.
- Every accepted first-seen event emits an `atlas_ledger` `record` intent.
- Duplicate events emit no new projection intents.
- `release` `observed` events emit a `discordos_update` `publish` intent with `requires_review`.
- `security_alert` `observed` events emit a `discordos_alerts` `alert` intent with `requires_review`.
- All routes keep `project_id`, `card_id`, `board_id`, `channel_id`, and `thread_id` as `null`.
- `external_mutation` remains denied everywhere.
- `unknown`, `empty`, `disabled`, `access_denied`, and `not_applicable` remain explicit states and are never rewritten into observed success.

## Boundary

- The runtime is backend-neutral.
- The runtime does not persist to SQLite, Postgres, Supabase, Vercel Queues, or any other ledger backend.
- The runtime does not call GitHub, Discord, Vercel, Supabase, Git, or any network service.
- The runtime does not format Discord messages or embed payloads.

## Verification

```powershell
node --test tests/github_event_admission.test.mjs
npm --prefix packages/atlas-contracts run validate
python ops/validation/validate_stack.py --ratchet --output-dir tmp/validation/github-event-admission-runtime
git diff --check
git diff --name-only
```

## Next Packet

- DiscordOS GitHub Projection Intent Dry-Run Consumer
