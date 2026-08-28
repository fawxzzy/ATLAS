import crypto from "node:crypto";
import { createReadStream } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { loadKnownSchema, validateJsonSchema } from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const CHECKPOINT_SCHEMA = "atlas.repair-and-learn-thread-corpus-checkpoint.v1";
const PROOF_SCHEMA = "atlas.repair-and-learn.initial-cursor-readback.v1";
const PLAN_SCHEMA = "atlas.repair-and-learn-corpus-review-plan.v1";
const DENOMINATOR_SCHEMA = "atlas.repair-and-learn.identity-binding.v1";
const LEASE_SCHEMA = "atlas.worker-lease.v2";
const LEASE_COMPONENT_ID = "atlas-workflow-optimization";
const WRITER_SCOPE = "atlas.workflow-optimization.repair-and-learn-checkpoint";
const CHECKPOINT_RESOURCE_ID = "repair-and-learn-thread-corpus/checkpoint";
const TASK_KEY_PATTERN = /^local\|([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;
const STABLE_TOKEN_PATTERN = /^[A-Za-z0-9._:/@+|-]+$/;
const workerLeaseSchemaRecord = await loadKnownSchema(LEASE_SCHEMA);
if (!workerLeaseSchemaRecord.ok) throw new Error(`Canonical worker lease schema unavailable: ${workerLeaseSchemaRecord.code}`);
const WORKER_LEASE_JSON_SCHEMA = workerLeaseSchemaRecord.schema;

export class InitialCursorInstallerError extends Error {}

function jsonBytes(value) { return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, "utf8"); }
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(value).digest("hex")}`; }
function clone(value) { return structuredClone(value); }
function requireObject(value, code) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new InitialCursorInstallerError(code);
}
function requireToken(value, code) {
  if (typeof value !== "string" || !STABLE_TOKEN_PATTERN.test(value)) throw new InitialCursorInstallerError(code);
}
function requireDigest(actual, expected, code) {
  if (typeof expected !== "string" || !/^sha256:[0-9a-f]{64}$/.test(expected) || actual !== expected) {
    throw new InitialCursorInstallerError(code);
  }
}
function checkpointSequence(checkpointId) {
  const match = /^raltcc_\d{8}_(\d+)$/.exec(checkpointId ?? "");
  if (!match) throw new InitialCursorInstallerError("CHECKPOINT_ID_UNSUPPORTED");
  return Number(match[1]);
}
function expectedNextCheckpointId(checkpointId, observedAt) {
  const parsed = new Date(observedAt);
  if (!Number.isFinite(parsed.getTime())) throw new InitialCursorInstallerError("PROOF_RECORDED_AT_INVALID");
  const day = parsed.toISOString().slice(0, 10).replaceAll("-", "");
  return `raltcc_${day}_${String(checkpointSequence(checkpointId) + 1).padStart(3, "0")}`;
}
function stablePlanId(plan) {
  const identity = {
    checkpoint_id: plan.checkpoint_id,
    task_key: plan.task_key,
    input_cursor: plan.selection.input_cursor,
    turn_ids: plan.selection.turn_ids,
    normalized_sha256: plan.normalization.sha256,
  };
  return `raltbp_${crypto.createHash("sha256").update(JSON.stringify(identity)).digest("hex").slice(0, 24)}`;
}
function markerKey(taskKey) { return `initial_cursor_install_${taskKey.slice("local|".length).replaceAll("-", "_")}`; }

function assertProof({ proof, taskKey, initialCursor, expectedSourceRefHash }) {
  requireObject(proof, "PROOF_INVALID");
  if (proof.schema !== PROOF_SCHEMA) throw new InitialCursorInstallerError("PROOF_SCHEMA_UNSUPPORTED");
  if (proof.task_key !== taskKey) throw new InitialCursorInstallerError("PROOF_TASK_KEY_MISMATCH");
  if (proof.source_ref_hash !== expectedSourceRefHash) throw new InitialCursorInstallerError("PROOF_SOURCE_REF_MISMATCH");
  if (proof.app_thread_identity_match !== true) throw new InitialCursorInstallerError("PROOF_THREAD_IDENTITY_UNVERIFIED");
  if (proof.source_storage_class !== "archived" || proof.source_status !== "notLoaded") {
    throw new InitialCursorInstallerError("SOURCE_NOT_CLOSED_ARCHIVED");
  }
  requireObject(proof.page, "PROOF_PAGE_INVALID");
  if (proof.page.order !== "newest_first" || proof.page.has_more !== true || proof.page.returned_turns !== 1) {
    throw new InitialCursorInstallerError("PROOF_PAGE_NOT_PARTIAL_NEWEST_FIRST");
  }
  if (proof.page.next_cursor !== initialCursor) throw new InitialCursorInstallerError("PROOF_CURSOR_MISMATCH");
  requireObject(proof.bootstrap_page_review, "PROOF_PRIVACY_INVALID");
  if (proof.bootstrap_page_review.raw_content_persisted !== false || proof.bootstrap_page_review.tool_output_persisted !== false) {
    throw new InitialCursorInstallerError("PROOF_RAW_CONTENT_PERSISTED");
  }
  requireObject(proof.source_post_read, "PROOF_SOURCE_POSTSTATE_INVALID");
  if (proof.source_post_read.closed !== true || proof.source_post_read.unchanged !== true) {
    throw new InitialCursorInstallerError("SOURCE_NOT_CLOSED_OR_STABLE");
  }
}

function assertDenominator({ denominator, taskKey, expectedSourceRefHash, expectedCheckpointId, expectedCheckpointSha256 }) {
  requireObject(denominator, "DENOMINATOR_INVALID");
  if (denominator.schema !== DENOMINATOR_SCHEMA) throw new InitialCursorInstallerError("DENOMINATOR_SCHEMA_UNSUPPORTED");
  requireObject(denominator.repair_and_learn_checkpoint, "DENOMINATOR_CHECKPOINT_INVALID");
  if (denominator.repair_and_learn_checkpoint.checkpoint_id !== expectedCheckpointId
    || `sha256:${denominator.repair_and_learn_checkpoint.sha256}` !== expectedCheckpointSha256) {
    throw new InitialCursorInstallerError("DENOMINATOR_CHECKPOINT_MISMATCH");
  }
  const matches = (Array.isArray(denominator.records) ? denominator.records : []).filter((record) => record?.task_key === taskKey);
  if (matches.length !== 1) throw new InitialCursorInstallerError("DENOMINATOR_TASK_IDENTITY_NOT_UNIQUE");
  const record = matches[0];
  if (record.source_ref_hash !== expectedSourceRefHash || record.source_state !== "METADATA_STABLE"
    || record.storage_class !== "archived" || record.content_cursor !== null || record.content_read !== false) {
    throw new InitialCursorInstallerError("DENOMINATOR_NEVER_READ_GATE_FAILED");
  }
  requireObject(denominator.privacy, "DENOMINATOR_PRIVACY_INVALID");
  if (denominator.privacy.raw_paths_persisted !== false || denominator.privacy.raw_filenames_persisted !== false
    || denominator.privacy.raw_content_read !== false || denominator.privacy.raw_content_persisted !== false) {
    throw new InitialCursorInstallerError("DENOMINATOR_PRIVACY_GATE_FAILED");
  }
}

function assertPlan({ plan, checkpoint, proof, taskKey, initialCursor, sourceIdentity, idempotent }) {
  requireObject(plan, "PLAN_INVALID");
  if (plan.schema !== PLAN_SCHEMA) throw new InitialCursorInstallerError("PLAN_SCHEMA_UNSUPPORTED");
  if (plan.task_key !== taskKey || plan.thread_id !== checkpoint.thread_id) {
    throw new InitialCursorInstallerError("PLAN_CHECKPOINT_CORRELATION_MISMATCH");
  }
  requireObject(plan.selection, "PLAN_SELECTION_INVALID");
  if (plan.selection.direction !== "immediately_preceding_input_cursor" || plan.selection.input_cursor !== initialCursor
    || !Number.isInteger(plan.selection.selected_turns) || plan.selection.selected_turns < 1
    || !Array.isArray(plan.selection.turn_ids) || plan.selection.turn_ids.length !== plan.selection.selected_turns
    || plan.selection.next_cursor !== plan.selection.turn_ids[0] || plan.selection.next_cursor === initialCursor
    || plan.selection.exhausted !== false || plan.selection.completed_content_reread !== false) {
    throw new InitialCursorInstallerError("PLAN_SELECTION_SEMANTICS_INVALID");
  }
  requireObject(plan.normalization, "PLAN_NORMALIZATION_INVALID");
  requireDigest(plan.normalization.sha256, plan.normalization.sha256, "PLAN_NORMALIZATION_DIGEST_INVALID");
  if (plan.plan_id !== stablePlanId(plan)) throw new InitialCursorInstallerError("PLAN_ID_NOT_CONTENT_ADDRESSED");
  requireObject(plan.privacy, "PLAN_PRIVACY_INVALID");
  if (plan.privacy.raw_messages_persisted !== false || plan.privacy.normalized_messages_persisted !== false
    || plan.privacy.metadata_plan_content_free !== true) throw new InitialCursorInstallerError("PLAN_RAW_CONTENT_PERSISTED");
  requireObject(plan.source, "PLAN_SOURCE_INVALID");
  if (plan.source.kind !== "LOCAL_CODEX_SESSION_JSONL" || plan.source.session_ref !== sourceIdentity.sessionRef
    || !plan.source.source_locator?.startsWith(`codex-session://local/${sourceIdentity.taskId}/lines/`)
    || plan.source.size_bytes !== sourceIdentity.size || plan.source.mtime_ms !== sourceIdentity.mtimeMs
    || plan.source.size_bytes !== proof.source_post_read.byte_size
    || plan.source.mtime_ms !== Date.parse(proof.source_post_read.modified_at)) {
    throw new InitialCursorInstallerError("PLAN_SOURCE_IDENTITY_MISMATCH");
  }
  if (!idempotent && plan.checkpoint_id !== expectedNextCheckpointId(checkpoint.checkpoint_id, proof.recorded_at)) {
    throw new InitialCursorInstallerError("PLAN_CHECKPOINT_ID_INCOMPATIBLE");
  }
}

function provenanceEntry({ initialCursor, proofDigest, planDigest, denominatorDigest, sourceIdentity, expectedSourceRefHash, plan }) {
  return { initial_cursor: initialCursor, proof_sha256: proofDigest, plan_sha256: planDigest,
    denominator_proof_sha256: denominatorDigest, source_sha256: sourceIdentity.sha256,
    source_ref_hash: expectedSourceRefHash, installed_checkpoint_id: plan.checkpoint_id };
}
function sameJson(left, right) { return JSON.stringify(left) === JSON.stringify(right); }

export function buildInitialCursorInstallation({ checkpointBytes, checkpoint, expectedCheckpointId,
  expectedCheckpointSha256, taskKey, initialCursor, proof, plan, denominator, expectedProofSha256,
  expectedPlanSha256, expectedDenominatorProofSha256, expectedSourceRefHash, sourceIdentity }) {
  requireObject(checkpoint, "CHECKPOINT_INVALID");
  if (checkpoint.schema !== CHECKPOINT_SCHEMA) throw new InitialCursorInstallerError("CHECKPOINT_SCHEMA_UNSUPPORTED");
  const taskMatch = TASK_KEY_PATTERN.exec(taskKey);
  if (!taskMatch) throw new InitialCursorInstallerError("TASK_KEY_INVALID");
  requireToken(initialCursor, "INITIAL_CURSOR_INVALID");
  requireDigest(expectedSourceRefHash, expectedSourceRefHash, "SOURCE_REF_HASH_INVALID");
  if (!Buffer.isBuffer(checkpointBytes)) throw new InitialCursorInstallerError("CHECKPOINT_BYTES_REQUIRED");
  const currentSha256 = sha256(checkpointBytes);
  const proofDigest = sha256(jsonBytes(proof)); const planDigest = sha256(jsonBytes(plan));
  const denominatorDigest = sha256(jsonBytes(denominator));
  requireDigest(proofDigest, expectedProofSha256, "PROOF_SHA256_MISMATCH");
  requireDigest(planDigest, expectedPlanSha256, "PLAN_SHA256_MISMATCH");
  requireDigest(denominatorDigest, expectedDenominatorProofSha256, "DENOMINATOR_SHA256_MISMATCH");
  assertProof({ proof, taskKey, initialCursor, expectedSourceRefHash });
  assertDenominator({ denominator, taskKey, expectedSourceRefHash, expectedCheckpointId, expectedCheckpointSha256 });
  requireObject(checkpoint.partial_review_cursors, "CHECKPOINT_CURSOR_MAP_INVALID");
  requireObject(checkpoint.coverage_counts, "CHECKPOINT_COVERAGE_INVALID");
  requireObject(checkpoint.validation, "CHECKPOINT_VALIDATION_INVALID");
  if (checkpoint.initial_cursor_provenance !== undefined) {
    requireObject(checkpoint.initial_cursor_provenance, "CHECKPOINT_PROVENANCE_MAP_INVALID");
  }
  if (!Number.isInteger(checkpoint.coverage_counts.partial_content_review)
    || checkpoint.coverage_counts.partial_content_review !== Object.keys(checkpoint.partial_review_cursors).length) {
    throw new InitialCursorInstallerError("CHECKPOINT_PARTIAL_DENOMINATOR_INCONSISTENT");
  }
  requireObject(sourceIdentity, "SOURCE_ACTION_TIME_IDENTITY_INVALID");
  if (sourceIdentity.taskId !== taskMatch[1] || sourceIdentity.closed !== true) {
    throw new InitialCursorInstallerError("SOURCE_ACTION_TIME_IDENTITY_MISMATCH");
  }
  const entry = provenanceEntry({ initialCursor, proofDigest, planDigest, denominatorDigest, sourceIdentity, expectedSourceRefHash, plan });
  const existingCursor = checkpoint.partial_review_cursors[taskKey];
  const idempotent = existingCursor === initialCursor && sameJson(checkpoint.initial_cursor_provenance?.[taskKey], entry);
  assertPlan({ plan, checkpoint, proof, taskKey, initialCursor, sourceIdentity, idempotent });
  const validationKey = markerKey(taskKey);
  const marker = `PASS_PROOF_${proofDigest.slice(7).toUpperCase()}_PLAN_${planDigest.slice(7).toUpperCase()}_SOURCE_${sourceIdentity.sha256.slice(7).toUpperCase()}`;
  if (idempotent && checkpoint.validation[validationKey] === marker) {
    return { status: "already-installed", changed: false, checkpoint, currentSha256, outputSha256: currentSha256,
      proofDigest, planDigest, denominatorDigest, sourceDigest: sourceIdentity.sha256 };
  }
  if (existingCursor !== undefined) throw new InitialCursorInstallerError("TASK_CURSOR_ALREADY_PRESENT_DIFFERENT_OR_UNPROVEN");
  if (checkpoint.checkpoint_id !== expectedCheckpointId) throw new InitialCursorInstallerError("CHECKPOINT_ID_DRIFT");
  requireDigest(currentSha256, expectedCheckpointSha256, "CHECKPOINT_SHA256_DRIFT");
  const nextCheckpoint = clone(checkpoint);
  nextCheckpoint.checkpoint_id = plan.checkpoint_id; nextCheckpoint.recorded_at = proof.recorded_at;
  nextCheckpoint.partial_review_cursors[taskKey] = initialCursor;
  nextCheckpoint.coverage_counts.partial_content_review += 1;
  nextCheckpoint.initial_cursor_provenance ??= {}; nextCheckpoint.initial_cursor_provenance[taskKey] = entry;
  nextCheckpoint.validation[validationKey] = marker;
  if (Array.isArray(nextCheckpoint.next) && nextCheckpoint.next.length > 0) {
    const partialCount = Object.keys(nextCheckpoint.partial_review_cursors).length;
    nextCheckpoint.next[0] = `Continue bounded content review across the remaining ${nextCheckpoint.coverage_counts.remaining_content_review} readable tasks by resuming one of ${partialCount} partial tasks from its exact durable cursor.`;
  }
  const outputBytes = jsonBytes(nextCheckpoint);
  return { status: "ready-to-install", changed: true, checkpoint: nextCheckpoint, outputBytes,
    currentSha256, outputSha256: sha256(outputBytes), proofDigest, planDigest, denominatorDigest, sourceDigest: sourceIdentity.sha256 };
}

async function readJsonBytes(target, code) {
  try { const bytes = await fs.readFile(target); return { bytes, value: JSON.parse(bytes.toString("utf8")), sha256: sha256(bytes) }; }
  catch (error) { throw new InitialCursorInstallerError(`${code}: ${error.message}`); }
}
async function hashFile(target) {
  const hash = crypto.createHash("sha256");
  await new Promise((resolve, reject) => { const stream = createReadStream(target); stream.on("data", (chunk) => hash.update(chunk)); stream.on("error", reject); stream.on("end", resolve); });
  return `sha256:${hash.digest("hex")}`;
}
async function findTaskSessionFiles(root, taskId) {
  const matches = []; const pending = [root];
  while (pending.length > 0) {
    const current = pending.pop();
    let entries;
    try { entries = await fs.readdir(current, { withFileTypes: true }); }
    catch (error) { if (error.code === "ENOENT") throw new InitialCursorInstallerError("CANONICAL_ACTIVE_SESSION_ROOT_MISSING"); throw error; }
    for (const entry of entries) {
      const target = path.join(current, entry.name);
      if (entry.isDirectory()) pending.push(target);
      else if (entry.isFile() && entry.name.toLowerCase().endsWith(`-${taskId.toLowerCase()}.jsonl`)) matches.push(target);
    }
  }
  return matches;
}
async function readSourceIdentity(sourceFile, taskKey, expectedSourceSha256, canonicalCodexRoot) {
  const taskId = TASK_KEY_PATTERN.exec(taskKey)?.[1];
  const [canonicalRoot, canonicalSource] = await Promise.all([fs.realpath(canonicalCodexRoot), fs.realpath(sourceFile)]);
  const archiveRoot = await fs.realpath(path.join(canonicalRoot, "archived_sessions"));
  if (path.dirname(canonicalSource).toLowerCase() !== archiveRoot.toLowerCase()) {
    throw new InitialCursorInstallerError("SOURCE_OUTSIDE_CANONICAL_CODEX_ARCHIVE");
  }
  const activeMatches = await findTaskSessionFiles(path.join(canonicalRoot, "sessions"), taskId);
  if (activeMatches.length > 0) throw new InitialCursorInstallerError("SOURCE_TASK_PRESENT_IN_ACTIVE_SESSIONS");
  const before = await fs.stat(canonicalSource);
  if (!before.isFile()) throw new InitialCursorInstallerError("SOURCE_NOT_FILE");
  const basename = path.basename(canonicalSource);
  if (!basename.toLowerCase().endsWith(`-${taskId.toLowerCase()}.jsonl`)) {
    throw new InitialCursorInstallerError("SOURCE_NOT_EXACT_ARCHIVED_SESSION");
  }
  const sourceSha256 = await hashFile(canonicalSource); requireDigest(sourceSha256, expectedSourceSha256, "SOURCE_SHA256_DRIFT");
  const after = await fs.stat(canonicalSource);
  if (before.size !== after.size || before.mtimeMs !== after.mtimeMs) throw new InitialCursorInstallerError("SOURCE_CHANGED_DURING_ACTION_TIME_READ");
  return { taskId, size: after.size, mtimeMs: Math.trunc(after.mtimeMs), sha256: sourceSha256,
    sessionRef: `archived_sessions/${basename}`, closed: true };
}
function validateLease({ lease, leaseDigest, options, now = Date.now() }) {
  const schemaErrors = validateJsonSchema(lease, WORKER_LEASE_JSON_SCHEMA);
  if (schemaErrors.length > 0) throw new InitialCursorInstallerError(`LEASE_SCHEMA_INVALID: ${schemaErrors.join("; ")}`);
  requireDigest(leaseDigest, options.expectedLeaseSha256, "LEASE_SHA256_MISMATCH");
  if (lease.lease_id !== options.expectedLeaseId || lease.job_id !== options.expectedJobId
    || lease.component_id !== LEASE_COMPONENT_ID || lease.writer_scope !== WRITER_SCOPE || lease.status !== "active"
    || lease.owner.worker_id !== options.expectedOwnerWorkerId || lease.owner.thread_id !== options.expectedOwnerThreadId
    || path.resolve(lease.workspace.root).toLowerCase() !== path.resolve(options.expectedLeaseWorkspaceRoot).toLowerCase()) {
    throw new InitialCursorInstallerError("LEASE_IDENTITY_OR_STATE_INVALID");
  }
  const acquired = Date.parse(lease.acquired_at);
  const expires = Date.parse(lease.expires_at);
  if (!Number.isFinite(acquired) || acquired > now || !Number.isFinite(expires) || expires <= now || expires <= acquired) {
    throw new InitialCursorInstallerError("LEASE_EXPIRED_OR_TIME_INVALID");
  }
  const resource = lease.resources?.find((item) => item?.resource_id === CHECKPOINT_RESOURCE_ID);
  if (!resource || resource.kind !== "custom" || resource.exclusive !== true) {
    throw new InitialCursorInstallerError("LEASE_CHECKPOINT_RESOURCE_NOT_EXCLUSIVE");
  }
}
async function persistRollback({ rollbackDir, checkpointId, preimageSha256, checkpointBytes }) {
  await fs.mkdir(rollbackDir, { recursive: true }); const target = path.join(rollbackDir, `${checkpointId}.${preimageSha256.slice(7)}.json`);
  try { await fs.writeFile(target, checkpointBytes, { flag: "wx" }); }
  catch (error) { if (error.code !== "EEXIST") throw error; if (!(await fs.readFile(target)).equals(checkpointBytes)) throw new InitialCursorInstallerError("ROLLBACK_PREIMAGE_COLLISION"); }
  return target;
}
async function writeAtomic(target, bytes) {
  const temporary = `${target}.tmp-${process.pid}-${crypto.randomUUID()}`; await fs.writeFile(temporary, bytes, { flag: "wx" });
  try { await fs.rename(temporary, target); } catch (error) { await fs.unlink(temporary).catch(() => {}); throw error; }
}

export async function installInitialCursor(options) {
  const [checkpointRecord, proofRecord, planRecord, denominatorRecord, sourceIdentity] = await Promise.all([
    readJsonBytes(options.checkpoint, "CHECKPOINT_UNREADABLE"), readJsonBytes(options.proof, "PROOF_UNREADABLE"),
    readJsonBytes(options.plan, "PLAN_UNREADABLE"), readJsonBytes(options.denominatorProof, "DENOMINATOR_UNREADABLE"),
    readSourceIdentity(options.sourceFile, options.taskKey, options.expectedSourceSha256, options.canonicalCodexRoot),
  ]);
  const built = buildInitialCursorInstallation({ checkpointBytes: checkpointRecord.bytes, checkpoint: checkpointRecord.value,
    expectedCheckpointId: options.expectedCheckpointId, expectedCheckpointSha256: options.expectedCheckpointSha256,
    taskKey: options.taskKey, initialCursor: options.initialCursor, proof: proofRecord.value, plan: planRecord.value,
    denominator: denominatorRecord.value, expectedProofSha256: options.expectedProofSha256,
    expectedPlanSha256: options.expectedPlanSha256, expectedDenominatorProofSha256: options.expectedDenominatorProofSha256,
    expectedSourceRefHash: options.expectedSourceRefHash, sourceIdentity });
  if (!built.changed || options.dryRun) {
    return { status: options.dryRun && built.changed ? "dry-run" : built.status, changed: false,
      checkpoint_id: built.checkpoint.checkpoint_id, checkpoint_sha256: built.outputSha256,
      proof_sha256: built.proofDigest, plan_sha256: built.planDigest, denominator_proof_sha256: built.denominatorDigest,
      source_sha256: built.sourceDigest, rollback_ref: null, raw_content_persisted: false,
      installed_cursor: built.checkpoint.partial_review_cursors[options.taskKey] };
  }
  if (!options.lease) throw new InitialCursorInstallerError("ACTIVE_CANONICAL_LEASE_REQUIRED");
  let leaseRecord = await readJsonBytes(options.lease, "LEASE_UNREADABLE");
  validateLease({ lease: leaseRecord.value, leaseDigest: leaseRecord.sha256, options });
  let actionTimeCheckpoint = await fs.readFile(options.checkpoint);
  if (sha256(actionTimeCheckpoint) !== built.currentSha256) throw new InitialCursorInstallerError("CHECKPOINT_ACTION_TIME_DRIFT");
  await readSourceIdentity(options.sourceFile, options.taskKey, options.expectedSourceSha256, options.canonicalCodexRoot);
  const rollbackTarget = await persistRollback({ rollbackDir: options.rollbackDir,
    checkpointId: checkpointRecord.value.checkpoint_id, preimageSha256: built.currentSha256, checkpointBytes: checkpointRecord.bytes });
  leaseRecord = await readJsonBytes(options.lease, "LEASE_UNREADABLE");
  validateLease({ lease: leaseRecord.value, leaseDigest: leaseRecord.sha256, options });
  actionTimeCheckpoint = await fs.readFile(options.checkpoint);
  if (sha256(actionTimeCheckpoint) !== built.currentSha256) throw new InitialCursorInstallerError("CHECKPOINT_PRE_REPLACE_DRIFT");
  await readSourceIdentity(options.sourceFile, options.taskKey, options.expectedSourceSha256, options.canonicalCodexRoot);
  if (options.beforeFinalPreReplace) await options.beforeFinalPreReplace();
  leaseRecord = await readJsonBytes(options.lease, "LEASE_UNREADABLE");
  validateLease({ lease: leaseRecord.value, leaseDigest: leaseRecord.sha256, options });
  actionTimeCheckpoint = await fs.readFile(options.checkpoint);
  if (sha256(actionTimeCheckpoint) !== built.currentSha256) throw new InitialCursorInstallerError("CHECKPOINT_FINAL_PRE_REPLACE_DRIFT");
  await writeAtomic(options.checkpoint, built.outputBytes);
  const installedBytes = await fs.readFile(options.checkpoint);
  if (sha256(installedBytes) !== built.outputSha256) throw new InitialCursorInstallerError("CHECKPOINT_POSTWRITE_DIGEST_MISMATCH");
  return { status: "installed", changed: true, checkpoint_id: built.checkpoint.checkpoint_id,
    checkpoint_sha256: built.outputSha256, preimage_sha256: built.currentSha256, proof_sha256: built.proofDigest,
    plan_sha256: built.planDigest, denominator_proof_sha256: built.denominatorDigest, source_sha256: built.sourceDigest,
    lease_sha256: leaseRecord.sha256, rollback_ref: path.basename(rollbackTarget), raw_content_persisted: false,
    installed_cursor: built.checkpoint.partial_review_cursors[options.taskKey] };
}

function parseArguments(argv) {
  const options = { dryRun: false, json: false };
  const names = new Map([["checkpoint", "checkpoint"], ["expected-checkpoint-id", "expectedCheckpointId"],
    ["expected-checkpoint-sha256", "expectedCheckpointSha256"], ["task-key", "taskKey"], ["initial-cursor", "initialCursor"],
    ["proof", "proof"], ["expected-proof-sha256", "expectedProofSha256"], ["plan", "plan"],
    ["expected-plan-sha256", "expectedPlanSha256"], ["denominator-proof", "denominatorProof"],
    ["expected-denominator-proof-sha256", "expectedDenominatorProofSha256"], ["source-file", "sourceFile"],
    ["canonical-codex-root", "canonicalCodexRoot"],
    ["expected-source-sha256", "expectedSourceSha256"], ["expected-source-ref-hash", "expectedSourceRefHash"],
    ["rollback-dir", "rollbackDir"], ["lease", "lease"], ["expected-lease-sha256", "expectedLeaseSha256"],
    ["expected-lease-id", "expectedLeaseId"], ["expected-job-id", "expectedJobId"],
    ["expected-owner-worker-id", "expectedOwnerWorkerId"], ["expected-owner-thread-id", "expectedOwnerThreadId"],
    ["expected-lease-workspace-root", "expectedLeaseWorkspaceRoot"]]);
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index]; if (argument === "--dry-run") { options.dryRun = true; continue; }
    if (argument === "--json") { options.json = true; continue; }
    if (!argument.startsWith("--") || !names.has(argument.slice(2))) throw new InitialCursorInstallerError(`UNSUPPORTED_ARGUMENT: ${argument}`);
    const value = argv[++index]; if (!value || value.startsWith("--")) throw new InitialCursorInstallerError(`ARGUMENT_VALUE_MISSING: ${argument}`);
    options[names.get(argument.slice(2))] = value;
  }
  const leaseFields = ["lease", "expectedLeaseSha256", "expectedLeaseId", "expectedJobId", "expectedOwnerWorkerId",
    "expectedOwnerThreadId", "expectedLeaseWorkspaceRoot"];
  for (const key of [...names.values()].filter((name) => !leaseFields.includes(name))) if (!options[key]) throw new InitialCursorInstallerError(`ARGUMENT_REQUIRED: ${key}`);
  if (!options.dryRun) for (const key of leaseFields) if (!options[key]) throw new InitialCursorInstallerError(`ARGUMENT_REQUIRED: ${key}`);
  return options;
}
export async function run(argv = process.argv.slice(2)) {
  const options = parseArguments(argv); const result = await installInitialCursor(options);
  process.stdout.write(`${JSON.stringify(result, null, options.json ? 2 : 0)}\n`); return result;
}
if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1].replaceAll("\\", "/")}`).href) {
  run().catch((error) => { process.stderr.write(`${error.name}: ${error.message}\n`); process.exitCode = 1; });
}
