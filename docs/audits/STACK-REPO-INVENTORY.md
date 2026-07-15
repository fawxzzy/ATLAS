# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `dirty_repo_count` counts only root-blocking repos; unmanaged owner-lane dirtiness remains visible as advisory dirtiness
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `13`
- Root-blocking dirty repo count: `1`
- Visible dirty repo count: `2`
- Advisory dirty repo count: `1`
- Release-eligible repo count: `4`
- Excluded surface count: `16`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:97e74fbff5942edc385d69a8484e27909401b7279eddafdf8bf051270f0916d7`

## Managed Repos

| Repo id | Path | Role | Playbook adoption status | Branch | Pinned commit | Current commit | Dirty | Root-blocking | Dirty blocks root | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | workflow-operator | verified | codex/stack-contracts-v2-cluster-2-producer | dd8e61a3a569ecab4f492c1af95e8b072efd78b6 | dd8e61a3a569ecab4f492c1af95e8b072efd78b6 | False | True | False | trusted | False | initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-local-data-gateway<br>initiative:continuity-manifest-post-convergence-lane-split-readiness<br>initiative:continuity-manifest-stack-readiness<br>initiative:continuity-manifest-vision-future-alignment |
| discordos | repos/DiscordOS | board-and-discord-writer | not-claimed | main | 3189a56b79daaae84c68f89fa4eb9552d91fc88a | 3189a56b79daaae84c68f89fa4eb9552d91fc88a | False | True | False | trusted | False | initiative:continuity-manifest-dependency-untangling<br>initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation |
| fitness | repos/fawxzzy-fitness | application | - | codex/fitness-qa-002-board-binding | - | b98fa17b90e62fbe191bf3c20c88bf674bc76c13 | False | False | False | adjacent | False | initiative:continuity-manifest-dependency-untangling<br>initiative:continuity-manifest-discord-os-feedback-workflow-canonicalization<br>initiative:continuity-manifest-discord-os-infrastructure-separation<br>initiative:continuity-manifest-local-data-gateway |
| foundation | repos/foundation | shared-contract-foundation | not-claimed | main | e0c2978e4f0d0b73aaee6fc5d14b982b78d89b97 | e0c2978e4f0d0b73aaee6fc5d14b982b78d89b97 | False | True | False | trusted | True | - |
| lifeline | repos/lifeline | local-operator | - | codex/path-discipline-warning-slice-lifeline | 54eeb56006099235723b60ce44de8a65e4c85889 | 54eeb56006099235723b60ce44de8a65e4c85889 | False | True | False | trusted | True | - |
| mazer | repos/mazer | application | - | codex/player-goal-default-colors | - | a537d2d17429bdf0482989c280373a6ea751f9c0 | True | False | False | adjacent | False | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | application | - | codex/path-discipline-warning-slice-nat1 | 404460d3717fab389407582048a9b9f228f26d39 | 404460d3717fab389407582048a9b9f228f26d39 | False | True | False | trusted | False | - |
| playbook | repos/playbook | governance-runtime | - | codex/repair-scheduled-demo-integration-ci | ee6907bd2d1d45ef87625cbd3382644dbb4fb199 | ee6907bd2d1d45ef87625cbd3382644dbb4fb199 | False | True | False | trusted | True | initiative:continuity-manifest-atlas-owned-repo-naming-canonicalization<br>initiative:initiative-fawxzzy-tech-plan-convergence |
| playbook-demo | repos/playbook-demo/playbook-demo | demo | - | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | True | False | trusted | False | - |
| socials-os | repos/socials-os | analytics-data-system | - | main | - | bfab3f8e66698219677ed083ffe4043338c5a4d5 | False | False | False | adjacent | False | - |
| stack | . | operator-layer | - | main | - | 37a5e0caa304ce710ac2a9bf17bfd55ce09da2bf | True | True | True | trusted | False | - |
| stream | repos/stream | application | - | main | 43769ba86d4c6ebc419ab9e7847c3843460a094f | 43769ba86d4c6ebc419ab9e7847c3843460a094f | False | True | False | trusted | False | - |
| trove | repos/trove | application | - | codex/path-discipline-warning-slice-trove | 437c7604adee02e0403d77f75162a6c5f232221f | 437c7604adee02e0403d77f75162a6c5f232221f | False | True | False | trusted | True | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| atlas_adjacent_checkout | repos/ATLAS | False | adjacent | False | metadata_only | Local ATLAS sibling checkout remains an adjacent non-canonical repo root and is not part of the governed stack member set. |
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
