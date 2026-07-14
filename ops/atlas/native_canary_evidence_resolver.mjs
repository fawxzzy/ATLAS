import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export class NativeCanaryEvidenceError extends Error {}

const RECOVERY_STATUSES = new Set(["resumed_and_verified", "owner_activity_observed_and_preserved"]);
const MUTATING_COMMAND_PATTERNS = [
  /\bgit\s+(?:add|commit|push|merge|rebase|reset|checkout|switch|clean|rm|mv|tag)\b/iu,
  /\b(?:Set-Content|Add-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item)\b/iu,
  /\bapply_patch\b/iu,
  /\b(?:npm|pnpm|yarn)\s+(?:install|add|remove|uninstall)\b/iu,
  /\bvercel\s+(?:deploy|promote|rollback)\b/iu,
  /\bsupabase\s+(?:db\s+push|migration|functions\s+deploy)\b/iu,
];

function digest(value) {
  return `sha256:${crypto.createHash("sha256").update(value).digest("hex")}`;
}

function requireString(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new NativeCanaryEvidenceError(`${label} must be a non-empty string.`);
  }
  return value;
}

function requireEmpty(value, label) {
  if (!Array.isArray(value) || value.length !== 0) {
    throw new NativeCanaryEvidenceError(`${label} must be an empty array in native evidence.`);
  }
}

function resolveContainedPath(base, relative, prefix, label) {
  requireString(relative, label);
  if (path.isAbsolute(relative)) throw new NativeCanaryEvidenceError(`${label} must be relative.`);
  const normalized = relative.replaceAll("\\", "/");
  if (!normalized.startsWith(prefix) || normalized.split("/").includes("..")) {
    throw new NativeCanaryEvidenceError(`${label} must stay under ${prefix}.`);
  }
  const resolved = path.resolve(base, relative);
  const containment = path.relative(base, resolved);
  if (!containment || containment.startsWith("..") || path.isAbsolute(containment)) {
    throw new NativeCanaryEvidenceError(`${label} escaped its evidence root.`);
  }
  return resolved;
}

function parseJsonMessage(value, label) {
  try {
    const parsed = JSON.parse(requireString(value, label));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("not_object");
    return parsed;
  } catch (error) {
    throw new NativeCanaryEvidenceError(`${label} is not a JSON object: ${error.message}`);
  }
}

function outputText(output) {
  if (typeof output === "string") return output;
  if (!Array.isArray(output)) return "";
  return output
    .filter((item) => item && typeof item === "object" && typeof item.text === "string")
    .map((item) => item.text)
    .join("\n");
}

function parseRollout(text, label) {
  const records = [];
  for (const [index, line] of text.split(/\r?\n/u).entries()) {
    if (!line.trim()) continue;
    try {
      records.push(JSON.parse(line));
    } catch (error) {
      throw new NativeCanaryEvidenceError(`${label} line ${index + 1} is invalid JSON: ${error.message}`);
    }
  }
  return records;
}

function resolveTurn(records, turnId, label) {
  const startIndex = records.findIndex((record) => record.type === "event_msg"
    && record.payload?.type === "task_started" && record.payload.turn_id === turnId);
  const completeIndex = records.findIndex((record, index) => index > startIndex
    && record.type === "event_msg" && record.payload?.type === "task_complete"
    && record.payload.turn_id === turnId);
  if (startIndex < 0 || completeIndex < 0) {
    throw new NativeCanaryEvidenceError(`${label} is missing native task_started/task_complete records.`);
  }
  const context = records.find((record, index) => index >= startIndex && index <= completeIndex
    && record.type === "turn_context" && record.payload?.turn_id === turnId)?.payload;
  if (!context) throw new NativeCanaryEvidenceError(`${label} is missing native turn_context.`);
  const complete = records[completeIndex].payload;
  const final = parseJsonMessage(complete.last_agent_message, `${label} final message`);
  const turnRecords = records.slice(startIndex, completeIndex + 1);
  if (turnRecords.some((record) => record.type === "event_msg" && record.payload?.type === "patch_apply_end"
    && record.payload.success !== false)) {
    throw new NativeCanaryEvidenceError(`${label} contains a native patch event.`);
  }
  const unsupportedTools = turnRecords.filter((record) => record.type === "response_item"
    && record.payload?.type === "custom_tool_call" && record.payload.name !== "exec");
  if (unsupportedTools.length > 0) throw new NativeCanaryEvidenceError(`${label} contains a non-read-only tool surface.`);
  const calls = turnRecords.filter((record) => record.type === "response_item"
    && record.payload?.type === "custom_tool_call" && record.payload.name === "exec");
  const outputs = new Map(turnRecords.filter((record) => record.type === "response_item"
    && record.payload?.type === "custom_tool_call_output")
    .map((record) => [record.payload.call_id, outputText(record.payload.output)]));
  if (calls.length === 0) throw new NativeCanaryEvidenceError(`${label} has no native command evidence.`);
  const commands = calls.map((record) => {
    if (MUTATING_COMMAND_PATTERNS.some((pattern) => pattern.test(record.payload.input))) {
      throw new NativeCanaryEvidenceError(`${label} contains a mutating command.`);
    }
    const text = outputs.get(record.payload.call_id) ?? "";
    return {
      call_id: record.payload.call_id,
      status: text.includes("Exit code: 0") ? "passed" : "failed",
      input_digest: digest(record.payload.input),
      output_digest: digest(text),
    };
  });
  return {
    turn_id: turnId,
    started_at: records[startIndex].timestamp,
    completed_at: records[completeIndex].timestamp,
    final,
    context,
    commands,
  };
}

function verificationPassed(value) {
  if (value === true) return true;
  if (typeof value === "string") return /(?:passed|completed|ok|match|preserved)/iu.test(value)
    && !/(?:blocked|failed|error)/iu.test(value);
  if (value && typeof value === "object") {
    return Object.values(value).every(verificationPassed);
  }
  return false;
}

function normalizeVerification(initial, recovery, projectId) {
  const source = recovery.final.verification ?? initial.final.verification;
  if (!source || typeof source !== "object" || Array.isArray(source) || !verificationPassed(source)) {
    throw new NativeCanaryEvidenceError(`${projectId} native verification did not resolve as passed.`);
  }
  return Object.entries(source).map(([name]) => ({
    command: `native-session:${projectId}:${name}`,
    status: "passed",
  }));
}

function runtimeFromContext(context) {
  const sandboxType = context.sandbox_policy?.type;
  return {
    model: requireString(context.model, "native runtime model"),
    reasoning: requireString(context.effort, "native runtime effort"),
    speed: "standard",
    permissions: sandboxType === "danger-full-access" ? "full-access" : sandboxType,
    approval_policy: requireString(context.approval_policy, "native approval policy"),
  };
}

export async function resolveNativeTaskEvidence(spec, { codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex") } = {}) {
  const sessionPath = resolveContainedPath(codexHome, spec.session_ref, "sessions/", "session_ref");
  const text = await fs.readFile(sessionPath, "utf8");
  const records = parseRollout(text, spec.session_ref);
  const session = records.find((record) => record.type === "session_meta")?.payload;
  if (!session || session.id !== spec.thread_id) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} session identity does not match its native rollout.`);
  }
  if (spec.initial_turn_id === spec.recovery_turn_id) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} requires a distinct native recovery turn.`);
  }
  const initial = resolveTurn(records, spec.initial_turn_id, `${spec.project_id} initial turn`);
  const recovery = resolveTurn(records, spec.recovery_turn_id, `${spec.project_id} recovery turn`);
  if (initial.final.project_id !== spec.project_id || initial.final.component_id !== spec.component_id) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} native project/component identity drift detected.`);
  }
  const recoveryStatus = recovery.final.recovery_status;
  if (!RECOVERY_STATUSES.has(recoveryStatus)) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} native recovery status is unsupported.`);
  }
  if (recovery.final.same_thread !== true) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} recovery did not attest the same native task.`);
  }
  if (recovery.final.terminal_status && recovery.final.terminal_status !== "completed") {
    throw new NativeCanaryEvidenceError(`${spec.project_id} native recovery did not complete.`);
  }
  if (recovery.commands.some((command) => command.status !== "passed")) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} native recovery contains a failed command.`);
  }
  if (initial.final.terminal_status === "completed" && initial.commands.some((command) => command.status !== "passed")) {
    throw new NativeCanaryEvidenceError(`${spec.project_id} completed initial turn contains a failed command.`);
  }
  const head = initial.final.head;
  if (!/^[0-9a-f]{40}$/iu.test(head)) throw new NativeCanaryEvidenceError(`${spec.project_id} native HEAD is invalid.`);
  const recoveryHead = recovery.final.current_head;
  if (recoveryHead && recoveryHead !== head) throw new NativeCanaryEvidenceError(`${spec.project_id} native HEAD drifted during recovery.`);
  requireEmpty(initial.final.changed_paths, `${spec.project_id} initial changed_paths`);
  requireEmpty(initial.final.authority_actions, `${spec.project_id} initial authority_actions`);
  requireEmpty(recovery.final.changed_paths, `${spec.project_id} recovery changed_paths`);
  requireEmpty(recovery.final.authority_actions, `${spec.project_id} recovery authority_actions`);
  requireEmpty(recovery.final.blockers, `${spec.project_id} recovery blockers`);

  return {
    ...spec,
    head,
    branch: requireString(initial.final.branch, `${spec.project_id} native branch`),
    runtime: runtimeFromContext(recovery.context),
    same_thread: true,
    terminal_status: "completed",
    recovery_status: recoveryStatus,
    recovery_checkpoint: recovery.final.recovery_checkpoint
      ?? `${spec.project_id} recovered in native turn ${spec.recovery_turn_id}.`,
    preexisting_dirty_path_count: recovery.final.current_dirty_path_count
      ?? recovery.final.preexisting_dirty_path_count
      ?? initial.final.preexisting_dirty_path_count
      ?? initial.final.preexisting_dirty_paths?.length
      ?? 0,
    verification: normalizeVerification(initial, recovery, spec.project_id),
    changed_paths: [],
    authority_actions: [],
    blockers: [],
    native_evidence: {
      session_ref: spec.session_ref,
      session_digest: digest(text),
      initial_turn: initial,
      recovery_turn: recovery,
    },
  };
}

export async function resolveBoardReadbackEvidence(source, { atlasRoot, recordedAt } = {}) {
  if (!atlasRoot) throw new NativeCanaryEvidenceError("atlasRoot is required for board evidence resolution.");
  const resolved = resolveContainedPath(atlasRoot, source.artifact_ref, "runtime/atlas/owner-lane-end-to-end-canary/", "board artifact_ref");
  const text = await fs.readFile(resolved, "utf8");
  const value = JSON.parse(text.replace(/^\uFEFF/u, ""));
  if (value.ok !== true || value.status !== "live_readback_ready") {
    throw new NativeCanaryEvidenceError("Resolved DiscordOS board artifact is not live-readback ready.");
  }
  const receiptId = value.readbackReceiptId ?? value.receiptId;
  if (receiptId !== source.expected_receipt_id) {
    throw new NativeCanaryEvidenceError("Resolved DiscordOS board receipt identity drift detected.");
  }
  if (value.writerAuthority !== "discordos" || value.callsDiscordApi !== true) {
    throw new NativeCanaryEvidenceError("Resolved board artifact lacks DiscordOS live-writer provenance.");
  }
  if (value.externalMutation !== "not_performed" || value.destructive !== false
    || value.sendsMessages !== false || value.writesArtifacts !== false) {
    throw new NativeCanaryEvidenceError("Resolved board artifact reports external mutation authority.");
  }
  const observedAt = Date.parse(value.observedAt);
  const receiptAt = Date.parse(recordedAt);
  if (!Number.isFinite(observedAt) || !Number.isFinite(receiptAt)) {
    throw new NativeCanaryEvidenceError("Board observation and canary receipt require ISO timestamps.");
  }
  const ageMs = receiptAt - observedAt;
  if (ageMs < 0 || ageMs > 5 * 60 * 1000) {
    throw new NativeCanaryEvidenceError("Resolved board artifact is stale or temporally inconsistent.");
  }
  return {
    ok: value.ok,
    status: value.status,
    board_id: value.boardId,
    observed_board_version: value.observedBoardVersion,
    checked_card_count: value.checkedCardCount,
    ready_card_count: value.readyCardCount,
    correlated_card_count: value.correlatedCardCount,
    idempotency_correlated_card_count: value.idempotencyCorrelatedCardCount,
    receipt_id: receiptId,
    writer_authority: value.writerAuthority,
    calls_discord_api: value.callsDiscordApi,
    external_mutation: value.externalMutation,
    observed_at: value.observedAt,
    source_artifact_ref: source.artifact_ref,
    source_digest: digest(text),
  };
}
