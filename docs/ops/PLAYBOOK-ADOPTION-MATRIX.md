# Playbook Adoption Matrix

This root-owned read model projects operational Playbook adoption for governed inventory components. It consumes declaration posture from `docs/registry/STACK-REPO-INVENTORY.json` and owner evidence through the validators and report projection in `ops/atlas/playbook_contract.py`. Owner repositories and their exports remain read-only.

## Operational Status Legend

- `missing`: no accepted manifest declaration and no valid owner proof that can be correlated safely
- `not_claimed`: the canonical manifest posture is explicitly `not-claimed`
- `declared`: an accepted profile/version declaration exists, but verification is absent or not current
- `verified`: the declaration agrees with a root-valid owner adoption export and verification receipt, the receipt is fresh, and declared or receipted owner HEAD/ref values agree with current inventory truth
- `stale`: otherwise valid, agreeing evidence is older than the freshness limit or names a prior owner HEAD/ref
- `conflicting`: declaration profile/version and owner evidence disagree, or owner proof lacks the required matching root declaration
- `blocked`: evidence cannot be parsed, fails the reused root contract validators, has an invalid timestamp, or current owner identity/trust/state makes verification unsafe

Field presence never earns adoption. An empty or absent `playbook_adoption_status`, a Playbook-named field, a filename, a note, or any other keyword produces no operational maturity. The explicit `not-claimed` posture is negative-safe unless genuine owner proof creates a conflict that must be reconciled.

## Declaration And Evidence Contract

An accepted declaration uses `playbook_adoption_status` with `declared`, `adopted`, or `verified` plus non-empty bounded `playbook_adoption_profile` and `playbook_adoption_version` values. The projection does not maintain or guess a static profile catalog. `not-claimed` is normalized to `not_claimed`; empty and absent values mean no declaration.

`verified` requires every gate below:

1. the explicit manifest profile and version declaration is accepted
2. the repo-owned adoption export validates with `validate_repo_adoption_payload`
3. the repo-owned verification report validates with `validate_playbook_verification_report` and reports `verified`
4. the profile/version claim agrees with the manifest declaration
5. current inventory identity and trust are safe for promotion
6. any declared or receipted `owner_head`/`owner_ref` agrees with inventory `current_commit`/`current_ref`, with at least one current correlation value present
7. `summary.last_verified_at` is timezone-aware, not in the future, and no more than 30 days old

Timestamp parsing fails closed. Evidence older than 30 days or correlated to an earlier owner HEAD/ref is `stale`; malformed timestamps or unavailable correlation truth are non-green. Owner exports remain advisory inputs until the root completes all gates.

## Operational Rows And Compatibility

Schema `atlas.playbook_adoption_matrix.v2` emits one stable, sorted row per governed inventory component. Rows contain only bounded decision data: component id, operational classification, normalized declaration, profile/version, validation and verification state, freshness and HEAD correlation, short evidence refs, bounded reasons, and a legacy mapping.

`legacy_classification` is deterministic compatibility data only:

- `declared` and `verified` map to legacy `owner_lane_advisory_adoption`
- every other operational status maps to legacy `missing_adoption`

The legacy value is never the operational `classification`. Consumers should migrate to the seven v2 status names.

Run the live read-only projection instead of copying status claims into this document:

```powershell
python ops/atlas/playbook_adoption_matrix.py --json --scope owner
```

In particular, old static claims that Fitness or Mazer are verified are not authoritative. A live row is `verified` only while all declaration, validation, trust, freshness, and HEAD/ref gates above are satisfied.

## Doctrine And Cortex Separation

`playbook_sources`, doctrine consumer/signals, and `cortex_substrate_candidates` remain separate read-only catalog sections. They identify documentation, historical doctrine, consumers, patterns, rules, and failure modes for discovery or future curation. Historical docs and keyword-only catalog matches never participate in owner operational classification.

The root-owned Cortex subsystem is not invented as a second implementation owner. It receives an owner row only if it is a governed inventory component; without a compatible declaration and owner-evidence contract it remains `missing` or `not_claimed`. Cortex substrate candidates do not upgrade that result.
