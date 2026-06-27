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
- Dirty repo count: `8`
- Release-eligible repo count: `5`
- Excluded surface count: `17`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:15db474a116ea3360bf0298eaa0e1bf997e5307e9ad2acf66ed232d7001d76d2`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | codex/queue-or-registry-broader-execution-behavior | e4fcd7c607a4830d141634b8350e32d8dbaa47ef | e4fcd7c607a4830d141634b8350e32d8dbaa47ef | True | trusted | False | initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-local-data-gateway<br>initiative:continuity-manifest-post-convergence-lane-split-readiness<br>initiative:continuity-manifest-stack-readiness<br>initiative:continuity-manifest-vision-future-alignment |
| discordos | repos/DiscordOS | main | ff8f21cfec199f50728ddddea79ba7f546392663 | ff8f21cfec199f50728ddddea79ba7f546392663 | True | trusted | False | initiative:continuity-manifest-dependency-untangling<br>initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation |
| fitness | repos/fawxzzy-fitness | main | - | 616443b69c9d203efee8e3c7dd3f2a1a4f9cd1e3 | True | adjacent | False | initiative:continuity-manifest-dependency-untangling<br>initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation<br>initiative:continuity-manifest-local-data-gateway |
| foundation | repos/foundation | main | fd1cf0650cdbb732f1231aa47a6e43138dab9062 | fd1cf0650cdbb732f1231aa47a6e43138dab9062 | False | trusted | True | - |
| lifeline | repos/lifeline | codex/path-discipline-warning-slice-lifeline | 538f623a84b003e70dadd234e6ea3af642446a5f | 538f623a84b003e70dadd234e6ea3af642446a5f | False | trusted | True | - |
| mazer | repos/mazer | main | 269b02b955451ca1847efb5dde1e172b4c887bb8 | 269b02b955451ca1847efb5dde1e172b4c887bb8 | False | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | codex/path-discipline-warning-slice-nat1 | 63a4a7c159c41a7e98ad8708891743acf71431ed | 63a4a7c159c41a7e98ad8708891743acf71431ed | True | trusted | False | - |
| playbook | repos/playbook | codex/path-discipline-warning-slice-playbook | f27c36355da906a01a46a841779553002c259f9b | f27c36355da906a01a46a841779553002c259f9b | True | trusted | True | initiative:continuity-manifest-atlas-owned-repo-naming-canonicalization |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | - | e79d48fcf1b1f4b21d0b4720291006f61c0d472f | True | trusted | False | - |
| stream | repos/stream | main | bf2c9551225e6d3555122da9a72306556f50cdd8 | bf2c9551225e6d3555122da9a72306556f50cdd8 | True | trusted | False | - |
| trove | repos/trove | codex/path-discipline-warning-slice-trove | cd572452b627c6a03dbdb440f9b4e431d9b8ed98 | cd572452b627c6a03dbdb440f9b4e431d9b8ed98 | True | trusted | True | - |

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
| lifeline_operator_evidence_worktree | repos/lifeline-operator-evidence | False | trusted | False | full | Lifeline operator evidence is a branch worktree of the registered lifeline repo and remains a temporary non-canonical evidence lane outside the governed repo surface. |
| playbook_codex_adjacent_checkout | repos/fawxzzy-playbook-codex | False | adjacent | False | metadata_only | Local Playbook Codex checkout remains an adjacent non-canonical helper surface outside the governed stack member set. |
| repo_backups_archive_surface | repos/repo-backups | True | trusted | False | full | Legacy bundle and patch backup drop remains visible for recovery provenance but is not a source repo surface and should converge on packages/bundles and packages/patches. |
| trove_release_cutover_worktree | repos/trove-release-cutover | False | trusted | False | full | Trove release cutover is a branch worktree of the registered trove repo and remains a temporary non-canonical cutover lane outside the governed repo surface. |
| verta_core_archive | repos/Verta-Core.zip | False | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | False | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
| zachariah_redfield_adjacent_checkout | repos/ZachariahRedfield | True | adjacent | False | metadata_only | ZachariahRedfield checkout is an adjacent unmanaged repo and is outside the governed ATLAS release surface. |
| zachariahredfield_adjacent_checkout | repos/ZachariahRedfield | True | adjacent | False | metadata_only | Local ZachariahRedfield checkout remains an adjacent personal repo root and is not part of the governed stack member set. |
