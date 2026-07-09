# Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory first-implementation worker-cluster reconciliation

- Date: `2026-07-09`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root implementation-backed worker-cluster reconciliation`
- Marker movement: none

## Scope

This receipt reconciles the admitted ATLAS-root worker slice for:

- `ops/cortex/chatgpt_codex_role_inventory.py`
- `tests/test_cortex_chatgpt_codex_role_inventory.py`

The worker remains read-only and root-bounded.

## Worker Base Checkpoint

The worker was implemented on top of:

- `main@35819410dee9b35361324539e327893cb4b6d209`

The helper/test pair is currently a bounded ATLAS-root worktree slice in this session until the exact files are staged and committed.

## Implemented Helper

`ops/cortex/chatgpt_codex_role_inventory.py` now:

1. admits only the frozen root-owned doctrine sources for the dual-mode lane
2. rejects owner-repo, hidden-transcript, deploy/platform, secret, absolute, and traversal source paths
3. requires the core operating-model, admission, prompt-pack, and workflow-profile doctrine refs
4. deterministically classifies ChatGPT, Codex, Deep Research, Pro Chat, Normal Chat, ATLAS, Playbook, and Cortex roles when present in admitted doctrine
5. maps those roles only into admitted future targets:
   - `cortex_synthesis_interface`
   - `cortex_execution_interface`
   - `cortex_bridge`
   - `shared_atlas_substrate`
   - `shared_playbook_doctrine_substrate`
6. preserves explicit authority denials and split-brain risk output
7. writes optional output only to root-relative `tmp/**.json`
8. supports `--strict` for nonzero blocker exit handling

## CLI Contract Reconciled

The landed CLI is:

```text
python ops/cortex/chatgpt_codex_role_inventory.py
  [--json]
  [--source <root-relative admitted source ref>]...
  [--output <root-relative tmp report path>]
  [--strict]
```

## JSON Contract Reconciled

The landed output schema is:

```text
atlas.cortex.chatgpt_codex_role_inventory.v1
```

Top-level fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `role_inventory`
- `synthesis_roles`
- `execution_roles`
- `bridge_roles`
- `simulation_roles`
- `replacement_targets`
- `external_dependencies`
- `current_role_count`
- `mapped_role_count`
- `unmapped_role_count`
- `current_roles`
- `future_interface_targets`
- `shared_substrate_dependencies`
- `authority_denials`
- `forbidden_surfaces`
- `split_brain_risks`
- `warnings`
- `blockers`
- `safe_to_use`

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Proof

Focused worker tests:

```powershell
python -m unittest tests.test_cortex_chatgpt_codex_role_inventory -v
```

Role-inventory smoke:

```powershell
python ops/cortex/chatgpt_codex_role_inventory.py --json
```

Safe tmp-output smoke:

```powershell
python ops/cortex/chatgpt_codex_role_inventory.py --json --output tmp/cortex/cortex-role-inventory-smoke.json
```

Root validation:

```powershell
python ops/validation/validate_stack.py
```

Selector regression guard:

```powershell
python -m unittest tests.test_atlas_marker_knockout_selector -v
python ops/atlas/marker_knockout_selector.py --format json
```

## Reconciled Proof Results

- focused helper tests passed
- helper JSON smoke passed with `status=ok`
- safe tmp-output smoke passed with `status=ok` and wrote only `tmp/cortex/cortex-role-inventory-smoke.json`
- stack validation remained `critical=0 error=0 warning=0 info=0`
- selector regression tests remained green
- generic root selector still keeps this lane as a supporting `0%` marker behind the held Sandbox and earlier fall-through lanes

## Sensitive-Rejection Proof

The focused test suite proves:

1. ChatGPT synthesis roles are classified
2. Codex execution roles are classified
3. Deep Research, Pro Chat, and Normal Chat are classified when present in admitted doctrine
4. ATLAS governance role is classified
5. Playbook doctrine role is classified
6. Cortex future bridge and execution roles are classified
7. hidden transcript sources are rejected
8. owner-repo sources are rejected
9. deploy/platform/secret sources are rejected
10. absolute and traversal output paths are rejected
11. safe `tmp/**.json` output is accepted
12. deterministic top-level JSON ordering is preserved
13. `--strict` returns nonzero on blockers
14. authority denials remain preserved verbatim

## Authority Preservation

Preserved throughout this packet:

- no hidden transcript scraping
- no owner-repo mutation
- no deploy or platform mutation
- no secrets read
- no `.env*` read
- no marker movement
- no Book, manifest, selector, or receipt writeback from the helper

## Marker Decision

No marker move is claimed here.

`Cortex Dual-Mode Replacement Readiness` remains `0%`.

Reason:

- the worker implementation is real and proof-backed
- the role inventory is now implementation-backed for admitted root doctrine
- but this receipt intentionally does not claim the broader `20%` threshold and does not widen into Book/current-state/restart/manifest ratchets
- the safest next same-lane move is a marker-surface ratchet decision rather than a threshold jump

## Exact Next Packet

If root reopens this family explicitly, the next safe root-only packet should be:

```text
Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory marker-surface ratchet decision
```

That packet should decide whether the current implementation-backed role inventory justifies a broader read-model or marker adoption, or whether the lane should remain held at `0%` until broader evidence is admitted.
