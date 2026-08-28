# Repair-and-Learn initial cursor installer

## Purpose

`ops/atlas/install_repair_and_learn_initial_cursor.mjs` closes one narrow gap in
the existing Repair-and-Learn checkpoint lifecycle: it installs a source-proven
first cursor for a never-read, closed local Codex session. It extends the
existing checkpoint contract; it does not define a scheduler, queue, receipt,
memory system, or content-retention surface.

## Required evidence

The installer fails closed unless all of these agree:

- the current checkpoint ID and byte-level SHA-256 equal the bound preimage;
- the task key is one exact `local|<session-id>` identity and is absent from the
  current partial-cursor map;
- the content-addressed Census denominator proof identifies that exact task as
  unique, archived, metadata-stable, never read, and without a content cursor;
- the existing bootstrap readback identifies the same task, archived/closed
  status, an unchanged source, a newest-first partial page, and the exact
  `nextCursor`;
- the existing content-free review plan identifies the same task and input
  cursor, matches the source byte size and modification time, persists no raw or
  normalized messages, has a rederived content-addressed plan ID, and names the
  deterministic next checkpoint ID;
- the archived source filename binds the exact task UUID and its action-time
  SHA-256, byte size, and modification time still match the sealed evidence;
- the resolved source is directly under the caller-bound canonical Codex
  `archived_sessions` root and the same task UUID is absent from the canonical
  active `sessions` tree.

Only the proven initial cursor is installed. The older cursor prepared by the
review plan is deliberately not installed or advanced during bootstrap.

## Mutation and rollback

The write requires one full-schema-valid `atlas.worker-lease.v2` for the
canonical Repair-and-Learn checkpoint writer scope, exact component, job,
worker, thread, workspace, and exclusive custom checkpoint resource. Immediately
before replacement—after the final potentially long source hash—the tool
rechecks the full lease identity and expiry plus the checkpoint byte digest. It
stores the exact preimage under the caller-provided rollback directory using a
content-addressed filename and atomically replaces the checkpoint. The lease is
the canonical single-writer exclusion; the repeated digest check closes drift
between source verification and replacement.

The checkpoint records append-only provenance under the exact task key: the
installed cursor plus proof, plan, denominator, source, and opaque source-ref
digests. That task-keyed record makes a repeated identical invocation
`already-installed` even after unrelated later checkpoint evolution, without
overwriting another source's provenance. A conflicting or unproven existing
cursor, denominator mismatch, checkpoint drift, task drift, source drift,
inactive lease, active source, or privacy violation is terminal.

`--dry-run` computes and validates the exact postimage without changing the
checkpoint or creating a rollback file. Source proof must use fixtures or an
isolated copy; the canonical corpus checkpoint is not a test target.

## Source-proof boundary

The initial implementation is `LOCAL_ONLY_UNSTAGED` in an isolated worktree.
Publication is `HELD`. No current corpus checkpoint, raw conversation content,
provider, product repository, pull request, merge, deployment, credential,
deletion, or retention state is touched by source proof.
