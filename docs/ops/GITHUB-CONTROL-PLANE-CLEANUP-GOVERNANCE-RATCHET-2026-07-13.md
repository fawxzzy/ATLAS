# GitHub Control-Plane Cleanup Governance Ratchet

Date: `2026-07-13`

## Decision

The `cleanup_governance` measurement unit is complete for classification and authority posture. This ratchet does not authorize or perform branch deletion, worktree removal, pruning, archive, or any other cleanup mutation.

## Evidence

- Source inventory: `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`
- Machine-readable classification: `docs/registry/GITHUB-CLEANUP-RETENTION-CLASSIFICATION.latest.json`
- Human-readable classification: `docs/ops/GITHUB-CLEANUP-RETENTION-CLASSIFICATION-2026-07-13.md`
- Reusable classifier: `ops/atlas/github_cleanup_retention_audit.mjs`
- Classifier tests: `ops/atlas/test_github_cleanup_retention_audit.mjs`

The classifier reconciled the accepted inventory exactly:

| Candidate family | Accepted inventory | Explicitly classified | Unknown | Removal-safe |
|---|---:|---:|---:|---:|
| Local worktrees | 62 | 62 | 0 | 0 |
| Merged remote branches | 80 | 80 | 0 | 0 |

Local worktree retention classes:

| Retention class | Count | Meaning |
|---|---:|---|
| `dirty_uncommitted_work_hold` | 17 | Preserve uncommitted work. |
| `merged_clean_candidate_hold` | 33 | Head is reachable from the observed default ref; removal still needs explicit authority and a receipt. |
| `unmerged_branch_hold` | 10 | Head is not proven merged into the observed default ref. |
| `open_pull_request_hold` | 1 | Branch remains tied to accepted open-PR evidence. |
| `detached_reproduction_hold` | 1 | Detached reproduction/forensic evidence remains preserved. |

All 80 merged remote-branch candidates are `merged_remote_branch_candidate_hold`.

## Authority

- `deletion_authorized: false`
- `branch_deletion_authorized: false`
- `worktree_removal_authorized: false`
- `archive_authorized: false`
- `remote_mutation_performed: false`
- `local_removal_performed: false`
- `required_removal_receipt: required_before_removal`

Classification is not cleanup authority. Clean is not removal-safe. Any later cleanup must be a separate admitted mutation with fresh exclusions, exact targets, pre/post evidence, and correlated receipts.

## Marker Consequence

The accepted GitHub Control-Plane Integration denominator remains eight binary units.

Completed units are now:

1. `repository_inventory`
2. `parity_projection`
3. `actions_projection`
4. `open_work_hygiene`
5. `release_security_projection`
6. `cleanup_governance`
7. `stack_event_correlation`

The only incomplete unit is:

1. `discordos_projection`

The marker therefore moves from `6 / 8 = 75%` to `7 / 8 = 87.5%`.

The Atlas Full-System Re-evaluation marker remains `50%`. No other marker moves.

## Reusable Knowledge

**RULE - Classification is not cleanup authority.** A retention class can clear governance ambiguity without authorizing deletion.

**PATTERN - Inventory, classify, hold, then separately admit mutation.** Refresh candidates, assign explicit fail-closed classes, require receipts, and only then consider a bounded cleanup packet.

**FAILURE MODE - Clean means disposable.** Treating a clean or merged worktree as automatically removable can destroy active context, forensic evidence, or owner-owned recovery state.
