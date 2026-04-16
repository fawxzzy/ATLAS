# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `10`
- Dirty repo count: `7`
- Release-eligible repo count: `5`
- Excluded surface count: `2`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:6901f07c52c4bb7bcdbdc42a23820a589bd59a408bd1616b0ab4e7b5b2b310df`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | 6125e1800401cdcec30f35de0e8d64ac602dadab | 6125e1800401cdcec30f35de0e8d64ac602dadab | True | trusted | False | - |
| atlas | repos/fawxzzy-atlas | main | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | False | trusted | True | - |
| fitness | repos/fawxzzy-fitness | main | 9e9eaaef785f940f54c09731211878e6958353f2 | 9e9eaaef785f940f54c09731211878e6958353f2 | True | trusted | True | - |
| lifeline | repos/fawxzzy-lifeline | codex/startup-public-truth-reconcile | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | False | trusted | True | - |
| mazer | repos/fawxzzy-mazer | main | f98cebb3e856a09d1a171221cdff1ed687bc5c28 | f98cebb3e856a09d1a171221cdff1ed687bc5c28 | True | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | ce9643465d69f76a46d92d0db6ed855d117e1bbd | ce9643465d69f76a46d92d0db6ed855d117e1bbd | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | main | 4efc7b7a85c23ee41f5210051ff90664a1aee444 | 4efc7b7a85c23ee41f5210051ff90664a1aee444 | True | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | 4dd8d8888b95c0d6d6bbea45283283051c4499e8 | 4dd8d8888b95c0d6d6bbea45283283051c4499e8 | True | trusted | False | - |
| stream | repos/fawxzzy-stream | codex/fstrm-wave3-surface-base | e30944cd79bd2f2d18afc9bbd9bdfe6f7a04df0f | e30944cd79bd2f2d18afc9bbd9bdfe6f7a04df0f | True | trusted | False | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| verta_core_archive | repos/Verta-Core.zip | True | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | True | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
