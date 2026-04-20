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
- Dirty repo count: `9`
- Release-eligible repo count: `5`
- Excluded surface count: `2`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:417b889930911b37a14eecd80a80d82ae4c6c0899b1abdfe7bb7c69082288931`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | 55690aae00ba67b113f127274be9c534f7159ed8 | 55690aae00ba67b113f127274be9c534f7159ed8 | True | trusted | False | - |
| atlas | repos/fawxzzy-atlas | main | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | True | trusted | True | - |
| fitness | repos/fawxzzy-fitness | main | 8015991815c597bbdefae779f70acb92aacc7a30 | 8015991815c597bbdefae779f70acb92aacc7a30 | True | trusted | True | - |
| lifeline | repos/fawxzzy-lifeline | main | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | True | trusted | True | - |
| mazer | repos/fawxzzy-mazer | main | 847b3c61a51dc9fada74731304483b0ffab3e62a | 847b3c61a51dc9fada74731304483b0ffab3e62a | True | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | ce9643465d69f76a46d92d0db6ed855d117e1bbd | ce9643465d69f76a46d92d0db6ed855d117e1bbd | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | main | 9ce397e893e4007afbe93366770867ed64f66500 | 9ce397e893e4007afbe93366770867ed64f66500 | True | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | 9fb75a20982bf5e7cc311fa2bc85746322d042eb | 9fb75a20982bf5e7cc311fa2bc85746322d042eb | True | trusted | False | - |
| stream | repos/fawxzzy-stream | codex/fstrm-wave3-surface-base | e8da0053e7762886687a40ea154a665186f70f95 | e8da0053e7762886687a40ea154a665186f70f95 | True | trusted | False | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| verta_core_archive | repos/Verta-Core.zip | True | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | True | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
