# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `12`
- Dirty repo count: `5`
- Release-eligible repo count: `5`
- Excluded surface count: `17`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:0e8c2fa79b8dc1ed43977db31a824af25cd9c9dfa678b5c37b4ade115b56c8c1`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | ae95be3f733736f51afe12fd539ebba81fadee45 | ae95be3f733736f51afe12fd539ebba81fadee45 | False | trusted | False | initiative:continuity-manifest-local-data-gateway |
| discordos | repos/DiscordOS | main | 721db1c5fe87db2aeee8419d8bdcef65fdd5d198 | 721db1c5fe87db2aeee8419d8bdcef65fdd5d198 | False | trusted | False | initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation |
| fitness | repos/fawxzzy-fitness | main | - | b2a734fa64fb3b4f4994c6963bf8bb743af8876c | True | adjacent | False | initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation |
| foundation | repos/fawxzzy-foundation | main | a016da2f08f167747f7ae7c804c0d6840cb9514d | a016da2f08f167747f7ae7c804c0d6840cb9514d | False | trusted | True | - |
| lifeline | repos/fawxzzy-lifeline | codex/lifeline-release-replay-verification | 4589b4f332247b32e01931907f803e5ea5991e34 | 4589b4f332247b32e01931907f803e5ea5991e34 | True | trusted | True | - |
| mazer | repos/fawxzzy-mazer | codex/mazer-remove-pwa-install-surface | 021291d2b4f75379ab7e4c7891e302b54d4845c6 | 021291d2b4f75379ab7e4c7891e302b54d4845c6 | False | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | 412846a1baac6c0ce782ab9ab94530ccf4e89ff5 | 412846a1baac6c0ce782ab9ab94530ccf4e89ff5 | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | codex/playbook-sustain-docs-audit | eeddaf75e59a6202c12bcf268221c5b469ac2b3a | eeddaf75e59a6202c12bcf268221c5b469ac2b3a | True | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | - | 8d94f4b1bb77f2066baca61216ae7cff9c5458f9 | True | trusted | False | - |
| stream | repos/stream | main | bf2c9551225e6d3555122da9a72306556f50cdd8 | bf2c9551225e6d3555122da9a72306556f50cdd8 | False | trusted | False | - |
| trove | repos/fawxzzy-trove | codex/trove-brand-asset-sync | 0f5f9fe55bd21aa7f017173f1950d0bd063470c1 | 0f5f9fe55bd21aa7f017173f1950d0bd063470c1 | False | trusted | True | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| atlas_adjacent_checkout | repos/ATLAS | False | adjacent | False | metadata_only | Local ATLAS sibling checkout remains an adjacent non-canonical repo root and is not part of the governed stack member set. |
| cortex_adjacent_checkout | repos/fawxzzy-cortex | False | adjacent | False | metadata_only | Cortex checkout is present in the workspace as an adjacent repo but is not yet a governed ATLAS child-repo adoption target. |
| cortex_playbook_snapshot_archive | repos/CORTEX-AND-PLAYBOOK-20260408.zip | False | untrusted | False | metadata_only | Mixed-owner snapshot reference remains manifest-visible for provenance only and must not be treated as owner truth before owner-split review. |
| dev_workspace_snapshot_archive | repos/dev.zip | False | untrusted | False | metadata_only | Generic legacy workspace snapshot remains manifest-visible for provenance only and must stay out of normal repo and release flows until cataloged. |
| fitness_parity_recovery_adjacent_checkout | repos/fawxzzy-fitness-parity-recovery | False | adjacent | False | metadata_only | Fitness parity recovery checkout remains an adjacent recovery surface and is excluded from the governed stack topology. |
| fitness_reclone_adjacent_checkout | repos/fawxzzy-fitness.reclone.20260502-195639 | False | adjacent | False | metadata_only | Fitness reclone checkout remains an adjacent recovery surface and is excluded from the governed stack topology. |
| fitness_reclone_recovery_checkout | repos/fawxzzy-fitness.reclone.20260502-195639 | False | untrusted | False | metadata_only | Fitness reclone remains a historical recovery checkout outside the canonical child repo and should not count as active stack adoption. |
| fitness_recovered_adjacent_checkout | repos/fawxzzy-fitness-recovered | False | adjacent | False | metadata_only | Fitness recovered checkout remains an adjacent recovery surface and is excluded from the governed stack topology. |
| fitness_recovered_checkout | repos/fawxzzy-fitness-recovered | False | untrusted | False | metadata_only | Fitness recovered checkout remains a non-canonical recovery lane outside the governed child-repo release surface. |
| lifeline_operator_evidence_worktree | repos/fawxzzy-lifeline-operator-evidence | False | trusted | False | full | Lifeline operator evidence is a branch worktree of the registered lifeline repo and remains a temporary non-canonical evidence lane outside the governed repo surface. |
| playbook_codex_adjacent_checkout | repos/fawxzzy-playbook-codex | False | adjacent | False | metadata_only | Local Playbook Codex checkout remains an adjacent non-canonical helper surface outside the governed stack member set. |
| repo_backups_archive_surface | repos/repo-backups | True | trusted | False | full | Legacy bundle and patch backup drop remains visible for recovery provenance but is not a source repo surface and should converge on packages/bundles and packages/patches. |
| trove_release_cutover_worktree | repos/fawxzzy-trove-release-cutover | False | trusted | False | full | Trove release cutover is a branch worktree of the registered trove repo and remains a temporary non-canonical cutover lane outside the governed repo surface. |
| verta_core_archive | repos/Verta-Core.zip | False | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | False | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
| zachariah_redfield_adjacent_checkout | repos/ZachariahRedfield | True | adjacent | False | metadata_only | ZachariahRedfield checkout is an adjacent unmanaged repo and is outside the governed ATLAS release surface. |
| zachariahredfield_adjacent_checkout | repos/ZachariahRedfield | True | adjacent | False | metadata_only | Local ZachariahRedfield checkout remains an adjacent personal repo root and is not part of the governed stack member set. |
