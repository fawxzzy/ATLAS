import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  InitialCursorInstallerError,
  buildInitialCursorInstallation,
  installInitialCursor,
} from "../ops/atlas/install_repair_and_learn_initial_cursor.mjs";

const TASK_ID = "01a04414-5df5-7ac3-b7e2-5ef28612c7fc";
const TASK_KEY = `local|${TASK_ID}`;
const INITIAL_CURSOR = "01a0441a-7d6f-7b20-92bc-2f38d1d79430";
const OLDER_CURSOR = "01a04414-6112-77f1-a487-17a9899b4946";
const SOURCE_REF_HASH = `sha256:${"3".repeat(64)}`;

function bytes(value) { return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, "utf8"); }
function digest(value) { return `sha256:${crypto.createHash("sha256").update(value).digest("hex")}`; }
function planId(plan) {
  const identity = {
    checkpoint_id: plan.checkpoint_id,
    task_key: plan.task_key,
    input_cursor: plan.selection.input_cursor,
    turn_ids: plan.selection.turn_ids,
    normalized_sha256: plan.normalization.sha256,
  };
  return `raltbp_${crypto.createHash("sha256").update(JSON.stringify(identity)).digest("hex").slice(0, 24)}`;
}

function fixture() {
  const checkpoint = {
    schema: "atlas.repair-and-learn-thread-corpus-checkpoint.v1",
    checkpoint_id: "raltcc_20260827_182",
    thread_id: "01a03746-df21-7770-bf72-41adb70052b4",
    recorded_at: "2026-08-27T18:00:00.000Z",
    partial_review_cursors: { "local|aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "existing-cursor" },
    coverage_counts: { partial_content_review: 1, remaining_content_review: 2131 },
    validation: {},
    next: ["Continue the prior cursor."],
  };
  const proof = {
    schema: "atlas.repair-and-learn.initial-cursor-readback.v1",
    recorded_at: "2026-08-28T00:45:00.000Z",
    task_key: TASK_KEY,
    source_ref_hash: SOURCE_REF_HASH,
    app_thread_identity_match: true,
    source_storage_class: "archived",
    source_status: "notLoaded",
    page: { order: "newest_first", has_more: true, returned_turns: 1, next_cursor: INITIAL_CURSOR },
    bootstrap_page_review: { raw_content_persisted: false, tool_output_persisted: false },
    source_post_read: { closed: true, unchanged: true, byte_size: 12, modified_at: "2026-08-27T15:16:21.072Z" },
  };
  const plan = {
    schema: "atlas.repair-and-learn-corpus-review-plan.v1",
    plan_id: "pending",
    checkpoint_id: "raltcc_20260828_183",
    thread_id: checkpoint.thread_id,
    task_key: TASK_KEY,
    source: {
      kind: "LOCAL_CODEX_SESSION_JSONL",
      session_ref: `archived_sessions/rollout-test-${TASK_ID}.jsonl`,
      source_locator: `codex-session://local/${TASK_ID}/lines/1-2`,
      size_bytes: 12,
      mtime_ms: Date.parse(proof.source_post_read.modified_at),
    },
    selection: {
      direction: "immediately_preceding_input_cursor",
      input_cursor: INITIAL_CURSOR,
      selected_turns: 1,
      turn_ids: [OLDER_CURSOR],
      next_cursor: OLDER_CURSOR,
      exhausted: false,
      completed_content_reread: false,
    },
    normalization: { sha256: `sha256:${"4".repeat(64)}` },
    privacy: { raw_messages_persisted: false, normalized_messages_persisted: false, metadata_plan_content_free: true },
  };
  plan.plan_id = planId(plan);
  const denominator = {
    schema: "atlas.repair-and-learn.identity-binding.v1",
    repair_and_learn_checkpoint: { checkpoint_id: checkpoint.checkpoint_id, sha256: digest(bytes(checkpoint)).slice(7) },
    records: [{ task_key: TASK_KEY, source_ref_hash: SOURCE_REF_HASH, source_state: "METADATA_STABLE",
      storage_class: "archived", content_cursor: null, content_read: false }],
    privacy: { raw_paths_persisted: false, raw_filenames_persisted: false, raw_content_read: false, raw_content_persisted: false },
  };
  const sourceIdentity = { taskId: TASK_ID, size: 12, mtimeMs: plan.source.mtime_ms,
    sha256: `sha256:${"5".repeat(64)}`, sessionRef: plan.source.session_ref, closed: true };
  return { checkpoint, proof, plan, denominator, sourceIdentity };
}

function buildOptions(input) {
  const checkpointBytes = bytes(input.checkpoint);
  return {
    checkpointBytes,
    checkpoint: input.checkpoint,
    expectedCheckpointId: input.checkpoint.checkpoint_id,
    expectedCheckpointSha256: digest(checkpointBytes),
    taskKey: TASK_KEY,
    initialCursor: INITIAL_CURSOR,
    proof: input.proof,
    plan: input.plan,
    denominator: input.denominator,
    expectedProofSha256: digest(bytes(input.proof)),
    expectedPlanSha256: digest(bytes(input.plan)),
    expectedDenominatorProofSha256: digest(bytes(input.denominator)),
    expectedSourceRefHash: SOURCE_REF_HASH,
    sourceIdentity: input.sourceIdentity,
  };
}

async function materialize() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-initial-cursor-"));
  const input = fixture();
  const archived = path.join(root, "archived_sessions");
  await fs.mkdir(archived);
  await fs.mkdir(path.join(root, "sessions"));
  const sourceFile = path.join(archived, `rollout-test-${TASK_ID}.jsonl`);
  await fs.writeFile(sourceFile, "hello world\n", "utf8");
  const requestedTime = new Date("2026-08-27T15:16:21.072Z");
  await fs.utimes(sourceFile, requestedTime, requestedTime);
  const stat = await fs.stat(sourceFile);
  input.proof.source_post_read.byte_size = stat.size;
  input.proof.source_post_read.modified_at = new Date(Math.trunc(stat.mtimeMs)).toISOString();
  input.plan.source.size_bytes = stat.size;
  input.plan.source.mtime_ms = Math.trunc(stat.mtimeMs);
  input.plan.plan_id = planId(input.plan);
  const checkpoint = path.join(root, "checkpoint.json");
  const proof = path.join(root, "proof.json");
  const plan = path.join(root, "plan.json");
  const denominatorProof = path.join(root, "denominator.json");
  const lease = path.join(root, "lease.json");
  const rollbackDir = path.join(root, "rollback");
  const leaseValue = {
    contract_version: "atlas.worker-lease.v2",
    lease_id: "lease-test-001",
    job_id: "job-test-001",
    component_id: "atlas-workflow-optimization",
    writer_scope: "atlas.workflow-optimization.repair-and-learn-checkpoint",
    status: "active",
    acquired_at: "2026-08-28T00:00:00.000Z",
    expires_at: "2099-01-01T00:00:00.000Z",
    owner: { worker_id: "atlas-workflow-optimization", thread_id: "01a03746-df21-7770-bf72-41adb70052b4", turn_id: null },
    workspace: { root, worktree: null, branch: null },
    resources: [{ kind: "custom", resource_id: "repair-and-learn-thread-corpus/checkpoint", exclusive: true }],
    recovery: { strategy: "resume", checkpoint: "runtime/atlas/engineering-memory-tasks/repair-and-learn-thread-corpus/checkpoint.json" },
  };
  for (const [target, value] of [[checkpoint, input.checkpoint], [proof, input.proof], [plan, input.plan],
    [denominatorProof, input.denominator], [lease, leaseValue]]) await fs.writeFile(target, bytes(value));
  const options = {
    checkpoint, proof, plan, denominatorProof, sourceFile, canonicalCodexRoot: root, rollbackDir, lease,
    expectedCheckpointId: input.checkpoint.checkpoint_id,
    expectedCheckpointSha256: digest(bytes(input.checkpoint)),
    taskKey: TASK_KEY,
    initialCursor: INITIAL_CURSOR,
    expectedProofSha256: digest(bytes(input.proof)),
    expectedPlanSha256: digest(bytes(input.plan)),
    expectedDenominatorProofSha256: digest(bytes(input.denominator)),
    expectedSourceSha256: digest(Buffer.from("hello world\n")),
    expectedSourceRefHash: SOURCE_REF_HASH,
    expectedLeaseSha256: digest(bytes(leaseValue)),
    expectedLeaseId: leaseValue.lease_id,
    expectedJobId: leaseValue.job_id,
    expectedOwnerWorkerId: leaseValue.owner.worker_id,
    expectedOwnerThreadId: leaseValue.owner.thread_id,
    expectedLeaseWorkspaceRoot: root,
  };
  return { root, input, options };
}

test("build installs only the proven initial cursor with task-keyed provenance", () => {
  const input = fixture();
  const result = buildInitialCursorInstallation(buildOptions(input));
  assert.equal(result.status, "ready-to-install");
  assert.equal(result.checkpoint.partial_review_cursors[TASK_KEY], INITIAL_CURSOR);
  assert.notEqual(result.checkpoint.partial_review_cursors[TASK_KEY], OLDER_CURSOR);
  assert.equal(result.checkpoint.coverage_counts.partial_content_review, 2);
  assert.equal(result.checkpoint.initial_cursor_provenance[TASK_KEY].source_sha256, input.sourceIdentity.sha256);
});

test("write requires the canonical lease, retains rollback, and is idempotent after later checkpoint evolution", async () => {
  const { root, options } = await materialize();
  try {
    const installed = await installInitialCursor(options);
    assert.equal(installed.status, "installed");
    assert.equal(installed.installed_cursor, INITIAL_CURSOR);
    assert.equal((await fs.readdir(options.rollbackDir)).length, 1);
    const later = JSON.parse(await fs.readFile(options.checkpoint, "utf8"));
    later.checkpoint_id = "raltcc_20260828_184";
    later.recorded_at = "2026-08-28T01:00:00.000Z";
    later.validation.unrelated_later_proof = "PASS";
    await fs.writeFile(options.checkpoint, bytes(later));
    const repeated = await installInitialCursor(options);
    assert.equal(repeated.status, "already-installed");
    assert.equal(repeated.changed, false);
    assert.equal((await fs.readdir(options.rollbackDir)).length, 1);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test("proof, plan, denominator, and content-addressed plan identities are authenticated", () => {
  const input = fixture();
  const options = buildOptions(input);
  options.expectedProofSha256 = `sha256:${"0".repeat(64)}`;
  assert.throws(() => buildInitialCursorInstallation(options), /PROOF_SHA256_MISMATCH/);
  const altered = fixture(); altered.plan.plan_id = "raltbp_wrong";
  assert.throws(() => buildInitialCursorInstallation(buildOptions(altered)), /PLAN_ID_NOT_CONTENT_ADDRESSED/);
  const alteredDenominator = fixture(); alteredDenominator.denominator.records.push(alteredDenominator.denominator.records[0]);
  assert.throws(() => buildInitialCursorInstallation(buildOptions(alteredDenominator)), /DENOMINATOR_TASK_IDENTITY_NOT_UNIQUE/);
});

test("checkpoint partial denominator and bound checkpoint preimage must agree", () => {
  const inconsistent = fixture(); inconsistent.checkpoint.coverage_counts.partial_content_review = 0;
  inconsistent.denominator.repair_and_learn_checkpoint.sha256 = digest(bytes(inconsistent.checkpoint)).slice(7);
  assert.throws(() => buildInitialCursorInstallation(buildOptions(inconsistent)), /CHECKPOINT_PARTIAL_DENOMINATOR_INCONSISTENT/);
  const drift = fixture(); const options = buildOptions(drift); options.expectedCheckpointSha256 = `sha256:${"9".repeat(64)}`;
  assert.throws(() => buildInitialCursorInstallation(options), /DENOMINATOR_CHECKPOINT_MISMATCH|CHECKPOINT_SHA256_DRIFT/);
});

test("active, unstable, or action-time drifted sources fail closed", async () => {
  const active = fixture(); active.proof.source_status = "loaded";
  assert.throws(() => buildInitialCursorInstallation(buildOptions(active)), /SOURCE_NOT_CLOSED_ARCHIVED/);
  const unstable = fixture(); unstable.proof.source_post_read.unchanged = false;
  assert.throws(() => buildInitialCursorInstallation(buildOptions(unstable)), /SOURCE_NOT_CLOSED_OR_STABLE/);
  const { root, options } = await materialize();
  try {
    await fs.appendFile(options.sourceFile, "drift");
    await assert.rejects(() => installInitialCursor({ ...options, dryRun: true }), /SOURCE_SHA256_DRIFT/);
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test("source must remain in the canonical archive with no active-session collision", async () => {
  const first = await materialize();
  const copiedRoot = await fs.mkdtemp(path.join(os.tmpdir(), "atlas-lookalike-codex-"));
  try {
    const copiedArchive = path.join(copiedRoot, "archived_sessions");
    await fs.mkdir(copiedArchive); await fs.mkdir(path.join(copiedRoot, "sessions"));
    const copiedSource = path.join(copiedArchive, path.basename(first.options.sourceFile));
    await fs.copyFile(first.options.sourceFile, copiedSource);
    await assert.rejects(() => installInitialCursor({ ...first.options, sourceFile: copiedSource, dryRun: true }),
      /SOURCE_OUTSIDE_CANONICAL_CODEX_ARCHIVE/);
    const activeSource = path.join(first.root, "sessions", `rollout-active-${TASK_ID}.jsonl`);
    await fs.writeFile(activeSource, "active");
    await assert.rejects(() => installInitialCursor({ ...first.options, dryRun: true }),
      /SOURCE_TASK_PRESENT_IN_ACTIVE_SESSIONS/);
  } finally {
    await fs.rm(first.root, { recursive: true, force: true });
    await fs.rm(copiedRoot, { recursive: true, force: true });
  }
});

test("never-read denominator proof is mandatory", () => {
  const input = fixture(); input.denominator.records[0].content_read = true;
  assert.throws(() => buildInitialCursorInstallation(buildOptions(input)), /DENOMINATOR_NEVER_READ_GATE_FAILED/);
  const missing = fixture(); missing.denominator.records = [];
  assert.throws(() => buildInitialCursorInstallation(buildOptions(missing)), /DENOMINATOR_TASK_IDENTITY_NOT_UNIQUE/);
});

test("raw plan data and lookalike cursor state without provenance fail closed", () => {
  const raw = fixture(); raw.plan.privacy.raw_messages_persisted = true;
  assert.throws(() => buildInitialCursorInstallation(buildOptions(raw)), /PLAN_RAW_CONTENT_PERSISTED/);
  const lookalike = fixture(); lookalike.checkpoint.partial_review_cursors[TASK_KEY] = INITIAL_CURSOR;
  lookalike.checkpoint.coverage_counts.partial_content_review = 2;
  lookalike.denominator.repair_and_learn_checkpoint.sha256 = digest(bytes(lookalike.checkpoint)).slice(7);
  assert.throws(() => buildInitialCursorInstallation(buildOptions(lookalike)), InitialCursorInstallerError);
});

test("write requires an exact active exclusive lease", async () => {
  const { root, options } = await materialize();
  try {
    await assert.rejects(() => installInitialCursor({ ...options, lease: undefined }), /ACTIVE_CANONICAL_LEASE_REQUIRED/);
    const lease = JSON.parse(await fs.readFile(options.lease, "utf8"));
    lease.resources[0].exclusive = false;
    await fs.writeFile(options.lease, bytes(lease));
    const invalid = { ...options, expectedLeaseSha256: digest(bytes(lease)) };
    await assert.rejects(() => installInitialCursor(invalid), /LEASE_CHECKPOINT_RESOURCE_NOT_EXCLUSIVE/);
    const second = await materialize();
    try {
      const lookalike = JSON.parse(await fs.readFile(second.options.lease, "utf8"));
      delete lookalike.component_id;
      await fs.writeFile(second.options.lease, bytes(lookalike));
      await assert.rejects(() => installInitialCursor({ ...second.options, expectedLeaseSha256: digest(bytes(lookalike)) }),
        /LEASE_SCHEMA_INVALID/);
    } finally { await fs.rm(second.root, { recursive: true, force: true }); }
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});

test("final pre-replace lease and checkpoint checks reject drift after source hashing", async () => {
  const checkpointCase = await materialize();
  try {
    await assert.rejects(() => installInitialCursor({ ...checkpointCase.options,
      beforeFinalPreReplace: async () => fs.writeFile(checkpointCase.options.checkpoint, bytes({ drift: true })) }),
    /CHECKPOINT_FINAL_PRE_REPLACE_DRIFT/);
    assert.deepEqual(JSON.parse(await fs.readFile(checkpointCase.options.checkpoint, "utf8")), { drift: true });
  } finally { await fs.rm(checkpointCase.root, { recursive: true, force: true }); }
  const leaseCase = await materialize();
  try {
    await assert.rejects(() => installInitialCursor({ ...leaseCase.options,
      beforeFinalPreReplace: async () => {
        const changedLease = JSON.parse(await fs.readFile(leaseCase.options.lease, "utf8"));
        changedLease.expires_at = "2026-08-28T00:00:01.000Z";
        await fs.writeFile(leaseCase.options.lease, bytes(changedLease));
      } }), /LEASE_SHA256_MISMATCH/);
  } finally { await fs.rm(leaseCase.root, { recursive: true, force: true }); }
});

test("dry-run computes the exact postimage with zero filesystem effects", async () => {
  const { root, options } = await materialize();
  try {
    const before = await fs.readFile(options.checkpoint);
    const result = await installInitialCursor({ ...options, dryRun: true, lease: undefined });
    assert.equal(result.status, "dry-run");
    assert.equal(result.changed, false);
    assert.equal(result.raw_content_persisted, false);
    assert.ok(result.checkpoint_sha256.startsWith("sha256:"));
    assert.deepEqual(await fs.readFile(options.checkpoint), before);
    await assert.rejects(() => fs.stat(options.rollbackDir), { code: "ENOENT" });
  } finally { await fs.rm(root, { recursive: true, force: true }); }
});
