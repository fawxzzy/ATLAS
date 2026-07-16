# ADR: Signed and Versioned Atlas Bootstrap Manifest

- Status: Proposed candidate; not implemented
- Date: 2026-07-16

## Context

Atlas needs a small, durable starting point for recovery across machines,
sessions, execution surfaces, and future storage implementations. External
Creation OS research recommends one persistent root pointer, but also warns
against treating one file as the whole memory system.

Current Atlas truth is already distributed by authority and state class:

- stack topology and governance live in versioned root artifacts;
- owner product and code truth live in owner repositories;
- doctrine and profiles are owned by Playbook;
- interoperability contracts are Atlas-owned;
- retained operational state and receipts live under explicit `runtime/**`
  paths;
- durable imports and data live under `data/**`;
- packages and release artifacts live under `packages/**`;
- Cortex read models are derived and advisory;
- secrets remain outside default exports.

A bootstrap artifact must recover this hierarchy without becoming a second
source of truth, a secret bundle, a queue implementation, or a vendor lock.

## Proposed decision

Atlas will define a signed, versioned bootstrap manifest whose only purpose is
to point recovery tooling into governed truth.

The manifest is a minimal recovery pointer. It is not the memory fabric and it
does not contain all state.

### What it points to

The contract should support references to:

- the Atlas root and declared stack topology;
- subject identity and workspace profile references;
- current policy and approval-policy references;
- component, contract, owner, and repo registries;
- retained state catalogs and receipt indexes;
- durable import, artifact, and package catalogs;
- recovery checkpoints and previous manifest versions;
- signer trust, revocation, and key-rotation metadata;
- integrity metadata for every required recovery reference.

References must be portable and authority-aware. A pointer may identify a Git
revision, Atlas-relative path, content digest, owner registry entry, or later
backend-neutral locator. It must not silently copy the target body.

### Source hierarchy

Recovery follows the accepted Atlas source hierarchy:

1. current executable/local owner evidence and authenticated timestamped
   read-only external responses for their planes;
2. `stack.yaml` for topology and policy;
3. current validation receipts for health;
4. Atlas Book marker surfaces only with accepted receipt and continuity proof;
5. continuity and restart indexes as projections;
6. current owner-repository product and code evidence;
7. chats, delegations, and handoffs as intent evidence;
8. historical, archived, and external research as provenance.

The bootstrap manifest cannot promote a lower source above a higher source.

### Recovery behavior

Recovery must:

1. parse a supported contract version;
2. verify the manifest digest and detached signature before resolving mutable
   references;
3. verify that the signer is currently trusted for the manifest scope;
4. resolve topology, policy, owner, and contract roots before runtime state;
5. verify required reference integrity and freshness independently;
6. rebuild derived indexes and Cortex read models from higher-authority sources;
7. preserve unavailable or contradictory references as unknown or degraded;
8. emit a deterministic recovery receipt without granting execution authority.

Rollback must be able to select a prior signed manifest revision while still
revalidating every referenced source. A valid old signature is not proof that
old owner or runtime state is still current.

## What the manifest explicitly does not contain

- full chat transcripts, memories, documents, embeddings, or graph contents;
- copied owner-repository code, plans, or current runtime truth;
- secret values, private keys, provider credentials, or raw access tokens;
- the complete execution queue or a hidden scheduler state;
- generated indexes that cannot be rebuilt from governed sources;
- production deployment, publication, purchasing, or device authority;
- a requirement for PostgreSQL, Qdrant, Neo4j, Redis, MinIO, SQLite, or any
  other storage product;
- a guarantee that a referenced surface is healthy merely because it resolves.

## Provenance, signing, and versioning requirements

The future contract must include:

- a stable contract identifier and semantic version;
- a unique manifest instance identifier;
- a monotonic revision or immutable version identity;
- creation and update timestamps;
- prior-version or recovery-chain reference;
- canonical serialization rules before hashing or signing;
- digest algorithm and digest;
- signer identity or key fingerprint;
- detached signature reference or equivalent non-secret signature material;
- trust-scope, revocation, and rotation semantics;
- per-reference scope, authority class, locator, and integrity metadata;
- validation fixtures for valid, stale, tampered, revoked, missing, cyclic, and
  unsupported-version cases;
- a deterministic recovery receipt and negative test matrix.

Signing proves artifact integrity and signer identity within a trust policy. It
does not prove that every referenced system is current, healthy, safe, or
authorized for mutation.

## Backend neutrality

The contract must define locator and integrity semantics independently of a
storage product. Initial implementation may use files and Git references. A
later backend may be admitted only through an ADR and migration evidence that
preserves:

- source hierarchy and owner authority;
- deterministic resolution and replay;
- backup and restore;
- export portability;
- signature validation;
- rollback;
- observability;
- acceptable operational cost.

No deployed memory fabric is claimed by this ADR candidate.

## Unresolved implementation choices

**DEFERRED DECISION**:

- manifest schema format and canonical serialization;
- signature and key-management mechanism;
- signer trust root, custody, recovery, rotation, and revocation;
- storage location and replication policy;
- offline and cross-machine bootstrap behavior;
- reference freshness windows and mandatory versus optional references;
- recovery conflict policy and operator UX;
- integration with Atlas Contracts and future Atlas Control ledger semantics;
- initial fixture set, validator owner, and release process.

These choices require implementation research and explicit operator approval
where they affect secrets handling, retention, or platform linkage.

## Consequences

- Atlas gains a stable recovery entrypoint without collapsing distributed truth.
- Recovery can fail closed and explain which authority or reference is missing.
- Backends and indexes remain replaceable.
- Every implementation must carry signing, provenance, versioning, negative
  conformance, and recovery receipts from the first accepted version.
- The manifest becomes an additional contract to maintain, but not an
  additional owner of the data it references.

## Tradeoffs

- A minimal pointer requires multiple source systems to recover a full state.
- Signature and key lifecycle increase operational complexity.
- Backend neutrality requires more explicit locator and adapter contracts.
- Fail-closed recovery may leave Atlas degraded until an operator resolves a
  missing or contradictory source.

These costs are preferable to an opaque one-file memory system or a
vendor-bound bootstrap path.

## Rejected alternatives

### One file contains all Atlas memory

Rejected because it duplicates owner truth, mixes state classes, creates an
unbounded secret and corruption surface, and cannot preserve independent
authority or retention rules.

### Unsigned mutable pointer

Rejected because recovery could not distinguish trusted updates from
tampering, accidental replacement, or stale machine-local state.

### Vendor-specific bootstrap contract

Rejected because a storage choice would become part of Atlas identity and
recovery semantics before measured requirements justify it.

### Bootstrap grants execution authority

Rejected because recovery identity and integrity do not authorize external or
production side effects.

## Acceptance gate

This ADR remains proposed until a later packet supplies:

- an operator-ratified threat and recovery model;
- an accepted schema and canonicalization decision;
- key custody and rotation decision;
- valid and invalid fixtures;
- deterministic validator proof;
- a file-native reference implementation;
- restore, rollback, and tamper tests;
- explicit confirmation that no deployed memory backend is implied.
