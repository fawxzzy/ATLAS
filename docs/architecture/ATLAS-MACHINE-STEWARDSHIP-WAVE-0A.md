# ATLAS Machine Stewardship Wave 0A

## Status and boundary

Wave 0A establishes a versioned evidence plane. It does not establish a machine
management runtime.

- **ATLAS owns:** policy, contracts, observed state, desired state, proposals,
  validation reports, orchestration, and receipt correlation.
- **Lifeline owns in a future admitted wave:** deterministic local execution,
  operator interaction, bounded elevation, rollback, and execution receipts.
- **This slice implements:** five contracts, deterministic validation and
  reporting, redacted machine identity, and fixed-local-volume metadata.
- **This slice does not implement:** proposal evaluation, execution, elevation,
  optimization, deletion, quarantine, repair, installation, service or startup
  changes, security changes, scheduling, or runtime activation.

This separation prevents ATLAS from becoming a second local executor. A future
Lifeline adapter must consume an exact proposal, prove authority and preimage,
execute deterministic primitives, and return an
`atlas.machine-execution-receipt.v1` document.

## Contract set

| Contract | Purpose | Mutation authority |
| --- | --- | --- |
| `atlas.machine-observed-state.v1` | Redacted metadata and collector errors | None |
| `atlas.machine-desired-state.v1` | Policy-bound desired conditions | None |
| `atlas.machine-action-proposal.v1` | Proposed intent with risk and authority classification | None; `PROPOSED_ONLY` |
| `atlas.machine-execution-receipt.v1` | Future Lifeline execution result | Evidence only |
| `atlas.machine-policy.v1` | Authority, privacy, protected-zone, and collector rules | None |

All documents use draft 2020-12 JSON Schema. Canonical JSON sorts object keys,
preserves array order, emits compact UTF-8, and rejects non-finite numbers.
Observed-state normalization removes exactly the two declared volatile JSON
pointers: `/collected_at_utc` and `/observation_id`.

## Authority levels

| Level | Meaning | Executor |
| --- | --- | --- |
| L0 | Redacted metadata observation with no machine mutation | ATLAS evidence plane |
| L1 | Desired-state comparison and proposal construction only | ATLAS evidence plane |
| L2 | Bounded, reversible local action after an exact admission | Future Lifeline |
| L3 | Elevated, startup, service, or scheduled-task action with explicit operator approval | Future Lifeline |
| L4 | Destructive, recovery, quarantine, or security-sensitive action with dedicated safeguards | Future Lifeline |

Silence is never approval. Source validation, a proposal, or a clean review
never grants Lifeline execution authority.

## Privacy and protected zones

Wave 0A collectors:

- retain only a SHA-256 fingerprint of the host label;
- retain only a SHA-256 fingerprint of a volume serial;
- do not read file contents;
- do not inspect environment values;
- do not enumerate directories or large files;
- do not follow symbolic links, junctions, mount-point reparse targets, or
  other reparse points;
- do not hydrate cloud placeholders;
- do not traverse UNC paths or network shares;
- do not upload data;
- do not infer that a file is safe to delete because it is absent from an
  observation.

Protected zones include secrets, user profiles, cloud placeholders, network
shares, reparse targets, recovery partitions, and any future operator-defined
zone. A future collector must classify and test its boundary before it can
observe a protected zone.

## Collector design

The identity collector uses non-admin platform metadata and immediately hashes
the raw host label. The fixed-volume collector invokes PowerShell with an
explicit argument array, no shell, a bounded timeout, captured output, and
normalized exit status. Its query is limited to `Win32_LogicalDisk` rows with
`DriveType=3`; it does not traverse a volume.

One collector failure does not invalidate successful evidence from another
collector. Errors are structured as collector, code, redacted message, and
recoverability. Invalid or non-local volume rows are rejected independently.

## Deferred collector families

The following families remain explicitly deferred:

1. top-level directory aggregation and configurable large-file metadata scan;
2. WinGet, AppX/MSIX, and read-only uninstall-registry application inventory;
3. startup, services, scheduled tasks, and an optional already-installed
   Autoruns adapter;
4. developer-tool discovery;
5. bounded performance sampling;
6. recovery and security status collectors;
7. complete whole-machine baseline acceptance across all collector families.

No deferred family may be inferred from the existence of these contracts.

## Safe extension rules

A new collector requires a separate admitted path set and must:

1. define its metadata boundary and protected zones before implementation;
2. use explicit subprocess arguments, a bounded timeout, captured output, and
   normalized errors;
3. prove it performs no write, elevation, network upload, content read, reparse
   traversal, or cloud hydration;
4. isolate inaccessible resources without discarding other valid evidence;
5. declare every volatile field and prove deterministic nonvolatile output;
6. add fixtures, schema validation, negative boundary tests, and redaction
   tests;
7. remain evidence-only unless a separately admitted Lifeline primitive exists.

## Failure modes

- **Failure mode:** ATLAS directly executes a proposal.
  **Guard:** proposal status is `PROPOSED_ONLY`; execution boundary is
  `LIFELINE_REQUIRED`.
- **Failure mode:** a metadata scan becomes content discovery.
  **Guard:** Wave 0A has no filesystem traversal or file-reading API.
- **Failure mode:** inaccessible resources erase otherwise valid evidence.
  **Guard:** collector errors are isolated and reported alongside successful
  collector results.
- **Failure mode:** observation absence becomes deletion advice.
  **Guard:** the privacy contract fixes `deletion_safety_inferred` to `false`.
