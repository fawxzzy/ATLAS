# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `11`
- Dirty repo count: `10`
- Release-eligible repo count: `6`
- Excluded surface count: `2`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:c12849258d4b60abc3957bc7675bbca452b0fdbf87c608c70c4dd59eb8e9766a`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | 55690aae00ba67b113f127274be9c534f7159ed8 | 55690aae00ba67b113f127274be9c534f7159ed8 | True | trusted | False | - |
| atlas | repos/fawxzzy-atlas | main | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | d915c6d3d5cc86c3a9f5de8805c90ae4d0de73d8 | True | trusted | True | - |
| fitness | repos/fawxzzy-fitness | main | 199163f43587e53c46cb092bdda685ad80d376c2 | 199163f43587e53c46cb092bdda685ad80d376c2 | True | trusted | True | - |
| lifeline | repos/fawxzzy-lifeline | main | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | 7a3ed573dd391eb9429f2f2d158046de4cfaa9a1 | True | trusted | True | - |
| mazer | repos/fawxzzy-mazer | main | 847b3c61a51dc9fada74731304483b0ffab3e62a | 847b3c61a51dc9fada74731304483b0ffab3e62a | True | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | ce9643465d69f76a46d92d0db6ed855d117e1bbd | ce9643465d69f76a46d92d0db6ed855d117e1bbd | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | main | 9ce397e893e4007afbe93366770867ed64f66500 | 9ce397e893e4007afbe93366770867ed64f66500 | True | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | 3ad6c1dd5ae8e037c7113177851485a46de8e3d7 | 3ad6c1dd5ae8e037c7113177851485a46de8e3d7 | True | trusted | False | - |
| stream | repos/fawxzzy-stream | codex/fstrm-wave3-surface-base | e8da0053e7762886687a40ea154a665186f70f95 | e8da0053e7762886687a40ea154a665186f70f95 | True | trusted | False | - |
| trove | repos/fawxzzy-trove | main | 17329fe916cedcc011d7faaca949c53a93dc5e77 | 17329fe916cedcc011d7faaca949c53a93dc5e77 | True | trusted | True | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| verta_core_archive | repos/Verta-Core.zip | True | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | True | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
