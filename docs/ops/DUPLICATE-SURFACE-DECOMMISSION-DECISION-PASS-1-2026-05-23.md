# Duplicate Surface Decommission Decision Pass 1

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Decision and routing only
Status: Pass 1 complete
Depends on: `docs/ops/DUPLICATE-SURFACE-DECOMMISSION-INVENTORY-2026-05-23.md`

## Purpose

This pass converts the initial duplicate-surface inventory into explicit retention, quarantine, routing, or later-deletion decisions without deleting, moving, or modifying any surface.

## Decision rules used in this pass

1. Do not delete any source-like surface until its retention class, canonical owner, and verification requirements are explicit.
2. Do not normalize quarantined Verta surfaces into ordinary repo cleanup.
3. Do not treat `tmp/` presence alone as a deletion signal; retained evidence and historical snapshots remain valid if the canonical path is already proven.
4. Prefer routing decisions that reduce hidden source-of-truth ambiguity before taking filesystem cleanup action.

## High-priority surface decisions

| Surface | Current role | Decision | Why | Required verification before later removal or retention closeout |
| --- | --- | --- | --- | --- |
| `C:/ATLAS-standalone/fitness-release-main` | Standalone Fitness checkout outside canonical `repos/fawxzzy-fitness` | manual review, then either archive deeper or delete later | This is the most dangerous remaining duplicate-source surface because it is a dirty Fitness checkout outside canonical governance | Confirm whether the dirty delta contains unique retained evidence, release-cutover context, or unpreserved commits; if not, confirm it is fully superseded by canonical `repos/fawxzzy-fitness` and retained `tmp` evidence surfaces |
| `C:/ATLAS-worktrees/pr1-stack-lock-refresh` | External ATLAS worktree outside root | delete later if no unique work remains | The surface looks like stale duplicate ATLAS lineage, not canonical root, but it still needs a unique-commit check before deletion | Confirm merge base against `main`, check for unique commits or docs not preserved elsewhere, then remove worktree and branch in a later disposal pass if clear |
| `repos/fawxzzy-trove-release-cutover` | Temporary Trove cutover lane | retain as evidence for now | It is a clean non-canonical cutover lane with documented purpose; deleting it before a Trove-specific cutover closeout would be blind cleanup | Confirm whether its cutover intent is still referenced by active Trove deployment or recovery docs; if not, convert it into explicit archived evidence or later-delete candidate |
| `repos/fawxzzy-lifeline-operator-evidence` | Temporary Lifeline evidence lane | retain as evidence for now | It is documented as a non-canonical operator evidence surface rather than a mystery duplicate | Confirm whether any evidence inside still supports active Lifeline operator or recovery workflows; if not, archive or fold evidence into a governed retained-evidence structure |

## Supporting surface confirmations

| Surface | Current role | Decision | Why | Required verification before later removal or retention closeout |
| --- | --- | --- | --- | --- |
| `repos/Verta-Core` | Quarantined raw Verta surface | keep quarantined | Existing docs already classify it as untrusted and non-release | Dedicated Verta trust-gate review only; do not fold into ordinary cleanup |
| `repos/Verta-Core.zip` | Raw Verta archive artifact | keep quarantined archive | Same governance bucket as raw `Verta-Core` | Dedicated Verta trust-gate review only |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | Retained reference only | retain as reference for now | Canonical Fitness path is already proven, so this is no longer an active dependency; it still has rollback/reference value | Confirm no remaining operator doc or lane claims it as active source truth, then schedule later archival or deletion |
| `tmp/fitness-main-post-merge` | Historical evidence only | retain as historical evidence for now | It preserves post-merge history and is not on the active Fitness path | Confirm no current workflow references it for active source truth, then schedule later archive/delete decision |
| `tmp/atlas-qa-release-refresh-pr` | Stale filesystem residue only | delete later after manual filesystem cleanup pass | It is no longer an active worktree or branch blocker | Confirm no retained evidence value and remove in a later Windows/filesystem cleanup pass |

## Additional low-priority follow-up surfaces

These are not the main blocker set, but they should not remain ambiguous indefinitely.

| Surface | Decision | Why |
| --- | --- | --- |
| `C:/ATLAS-worktrees/remove-stale-cortex-contract-v2` | delete later after residue check | It no longer presents as a live worktree root and looks like orphaned residue |
| `repos/fawxzzy-fitness-discord-bot` | manual review, likely delete later | Empty or placeholder surface should either be given a documented owner/purpose or removed |
| `repos/fawxzzy-playbook-codex` | manual review | Adjacent non-canonical helper surface, but not an immediate production blocker |
| `repos/playbook-demo` | manual review | Example/demo surface should be explicitly retained or later deleted |
| `repos/ZachariahRedfield` | manual review | Adjacent personal repo surface is not part of current convergence lane, but should stay documented |
| `repos/repo-backups` | do not delete | Package-layer backup infrastructure, not a duplicate source repo |

## Pass 1 conclusions

1. No high-priority surface is ready for deletion without a focused follow-up check.
   The highest-risk surfaces either carry possible unique state, are intentionally retained evidence, or belong to quarantined trust-gate governance.

2. The next decommission win is decision tightening, not filesystem action.
   `fitness-release-main` and `pr1-stack-lock-refresh` are the two most likely future delete-or-archive candidates once their unique-state checks are complete.

3. Duplicate Surface Decommission is now out of discovery-only mode.
   The remaining work is to convert these routing decisions into explicit verification checklists and then later disposal/archive receipts.

## Recommended next package

Run `Duplicate Surface Decommission Verification Pass 2` focused only on:

- `C:/ATLAS-standalone/fitness-release-main`
- `C:/ATLAS-worktrees/pr1-stack-lock-refresh`
- `repos/fawxzzy-trove-release-cutover`
- `repos/fawxzzy-lifeline-operator-evidence`

That pass should answer the unique-state question for each surface and decide whether it becomes:

- retained evidence
- archived deeper
- safe delete later
- still blocked on manual review
