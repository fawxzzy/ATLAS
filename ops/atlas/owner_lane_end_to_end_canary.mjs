import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { buildBoardEvent } from "./native_board_correlation.mjs";
import {
  resolveBoardReadbackEvidence,
  resolveNativeTaskEvidence,
} from "./native_canary_evidence_resolver.mjs";
import { correlateNativeTask } from "./native_task_correlation.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const REQUIRED_PROJECTS = new Map([
  ["atlas", "atlas-root"],
  ["mazer", "mazer"],
  ["fitness", "fawxzzy-fitness"],
]);
const RECOVERY_STATUSES = new Set(["resumed_and_verified", "owner_activity_observed_and_preserved"]);

export class OwnerLaneEndToEndCanaryError extends Error {}

function requireString(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new OwnerLaneEndToEndCanaryError(`${label} must be a non-empty string.`);
  }
  return value;
}

function requireEmptyArray(value, label) {
  if (!Array.isArray(value) || value.length !== 0) {
    throw new OwnerLaneEndToEndCanaryError(`${label} must be an empty array.`);
  }
}

function safePath(inputPath, output = false) {
  const resolved = path.resolve(ROOT, inputPath);
  const relative = path.relative(ROOT, resolved).replaceAll("\\", "/");
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new OwnerLaneEndToEndCanaryError("Canary paths must resolve inside the Atlas root.");
  }
  const segments = relative.toLowerCase().split("/");
  if (segments.includes("secrets") || segments.some((segment) => segment === ".env" || segment.startsWith(".env."))) {
    throw new OwnerLaneEndToEndCanaryError("Canary paths cannot reference secret or env files.");
  }
  if (output && !relative.startsWith("runtime/atlas/owner-lane-end-to-end-canary/") && !relative.startsWith("tmp/")) {
    throw new OwnerLaneEndToEndCanaryError("Canary output must be under runtime/atlas/owner-lane-end-to-end-canary/ or tmp/.");
  }
  return { resolved, relative };
}

function parseArguments(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!["--input", "--output"].includes(argument)) {
      throw new OwnerLaneEndToEndCanaryError(`Unsupported argument: ${argument}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new OwnerLaneEndToEndCanaryError(`${argument} requires a value.`);
    options[argument.slice(2)] = value;
    index += 1;
  }
  if (!options.input || !options.output) throw new OwnerLaneEndToEndCanaryError("--input and --output are required.");
  return options;
}

function assertTask(task) {
  const projectId = requireString(task?.project_id, "task project_id");
  if (!REQUIRED_PROJECTS.has(projectId)) throw new OwnerLaneEndToEndCanaryError(`Unexpected canary project: ${projectId}.`);
  if (task.component_id !== REQUIRED_PROJECTS.get(projectId)) {
    throw new OwnerLaneEndToEndCanaryError(`Component identity drift for ${projectId}.`);
  }
  for (const key of ["job_id", "thread_id", "initial_turn_id", "recovery_turn_id", "head", "branch", "recovery_status"]) {
    requireString(task[key], `${projectId} ${key}`);
  }
  if (!/^[0-9a-f]{40}$/i.test(task.head)) throw new OwnerLaneEndToEndCanaryError(`${projectId} head must be a full commit SHA.`);
  if (task.initial_turn_id === task.recovery_turn_id) {
    throw new OwnerLaneEndToEndCanaryError(`${projectId} recovery must use a distinct turn in the same native task.`);
  }
  if (task.same_thread !== true) throw new OwnerLaneEndToEndCanaryError(`${projectId} recovery must remain in the same native task.`);
  if (task.terminal_status !== "completed") throw new OwnerLaneEndToEndCanaryError(`${projectId} did not complete after recovery.`);
  if (!RECOVERY_STATUSES.has(task.recovery_status)) throw new OwnerLaneEndToEndCanaryError(`${projectId} recovery status is unsupported.`);
  requireEmptyArray(task.changed_paths, `${projectId} changed_paths`);
  requireEmptyArray(task.authority_actions, `${projectId} authority_actions`);
  requireEmptyArray(task.blockers, `${projectId} blockers`);
  if (!Array.isArray(task.verification) || task.verification.length === 0) {
    throw new OwnerLaneEndToEndCanaryError(`${projectId} requires verification evidence.`);
  }
  for (const verification of task.verification) {
    requireString(verification.command, `${projectId} verification command`);
    if (verification.status !== "passed") throw new OwnerLaneEndToEndCanaryError(`${projectId} verification did not pass.`);
  }
  return task;
}

function jobEnvelope(task, recordedAt) {
  return {
    contract_version: "atlas.job-envelope.v2",
    job_id: task.job_id,
    component_id: task.component_id,
    project_id: task.project_id,
    created_at: recordedAt,
    objective: `Complete the ${task.project_id} read-only owner-lane orchestration canary.`,
    scope: {
      owner_repository: task.component_id,
      allowed_paths: [],
      forbidden_paths: ["secrets/**", "**/.env", "**/.env.*"],
    },
    runtime: task.runtime,
    authority: { external_mutations: [], production_deploy: false, destructive_actions: false },
    verification: {
      commands: task.verification.map((item) => item.command),
      evidence_required: ["read-only native task result", "same-thread recovery proof"],
    },
    correlations: { card_id: task.card_id ?? null, parent_job_id: null },
    expected_receipt_version: "atlas.execution-receipt.v2",
    extensions: { canary_version: "atlas.owner-lane-e2e-canary.v1" },
  };
}

function contextPacket(task, recordedAt) {
  return {
    contract_version: "atlas.context-packet.v2",
    context_id: `ctx-${task.job_id}`,
    job_id: task.job_id,
    component_id: task.component_id,
    assembled_at: recordedAt,
    sources: [{ kind: "repository", ref: task.context_ref, authority: "authoritative", digest: null }],
    rules: ["Preserve owner-task work and perform no authority action."],
    decisions: ["Use one read-only native task plus same-thread recovery."],
    risks: ["Concurrent owner work may change advisory dirty-state observations."],
  };
}

function evidenceBundle(task, recordedAt) {
  return {
    contract_version: "atlas.evidence-bundle.v2",
    bundle_id: `evb-${task.job_id}`,
    job_id: task.job_id,
    recorded_at: recordedAt,
    environment: { component_id: task.component_id, commit: task.head, branch: task.branch },
    evidence: [
      {
        kind: "source",
        ref: task.native_evidence.session_ref,
        status: "captured",
        digest: task.native_evidence.session_digest,
        summary: "Native Codex rollout resolved directly from the local task store.",
      },
      ...task.verification.map((item, index) => ({
        kind: "test",
        ref: `canary:${task.project_id}:verification:${index + 1}`,
        status: "passed",
        digest: task.native_evidence.recovery_turn.commands[index]?.output_digest ?? null,
        summary: item.command,
      })),
    ],
    classifications: ["verified"],
    extensions: {
      initial_turn_id: task.initial_turn_id,
      recovery_turn_id: task.recovery_turn_id,
      native_command_count: task.native_evidence.initial_turn.commands.length
        + task.native_evidence.recovery_turn.commands.length,
    },
  };
}

function workerLease(task, recordedAt) {
  return {
    contract_version: "atlas.worker-lease.v2",
    lease_id: `lease-${task.job_id}`,
    job_id: task.job_id,
    component_id: task.component_id,
    writer_scope: `read.${task.component_id}.owner-lane-canary`,
    status: "released",
    acquired_at: recordedAt,
    expires_at: recordedAt,
    renewed_at: null,
    released_at: recordedAt,
    owner: { worker_id: `native-${task.thread_id}`, thread_id: task.thread_id, turn_id: task.recovery_turn_id },
    workspace: { root: task.workspace_root, worktree: null, branch: task.branch },
    resources: [{
      kind: "custom",
      resource_id: `${task.component_id}:read-only-canary`,
      exclusive: false,
      metadata: { mode: "read-only", preexisting_dirty_path_count: task.preexisting_dirty_path_count ?? 0 },
    }],
    recovery: { strategy: "resume", checkpoint: task.recovery_checkpoint },
  };
}

function nativeTaskResult(task, recordedAt) {
  return {
    job_id: task.job_id,
    thread_id: task.thread_id,
    turn_id: task.recovery_turn_id,
    terminal_status: "completed",
    recorded_at: recordedAt,
    final_response: `${task.project_id} canary completed with recovery status ${task.recovery_status}.`,
    changed_paths: [],
    commits: [],
    evidence_refs: [`canary:${task.project_id}:initial-turn:${task.initial_turn_id}`, `canary:${task.project_id}:recovery-turn:${task.recovery_turn_id}`],
    blockers: [],
    follow_up: [],
    authority_actions: [],
    verification: task.verification.map((item, index) => ({
      command: item.command,
      status: "passed",
      evidence_refs: [`canary:${task.project_id}:verification:${index + 1}`],
    })),
    branch: task.branch,
    worktree: null,
    runtime_effective: task.runtime,
  };
}

function assertBoardReadback(readback) {
  if (readback?.ok !== true || readback.status !== "live_readback_ready") {
    throw new OwnerLaneEndToEndCanaryError("DiscordOS board readback must be live and ready.");
  }
  if (readback.writer_authority !== "discordos" || readback.external_mutation !== "not_performed") {
    throw new OwnerLaneEndToEndCanaryError("DiscordOS board readback authority drift detected.");
  }
  const checked = readback.checked_card_count;
  if (!Number.isInteger(checked) || checked <= 0 || readback.ready_card_count !== checked
      || readback.correlated_card_count !== checked || readback.idempotency_correlated_card_count !== checked) {
    throw new OwnerLaneEndToEndCanaryError("DiscordOS board readback counts do not prove complete correlation.");
  }
  requireString(readback.receipt_id, "board readback receipt_id");
}

export async function buildOwnerLaneEndToEndCanary(input, { atlasRoot = ROOT, codexHome } = {}) {
  if (input?.contract_version !== "atlas.owner-lane-e2e-canary-input.v2") {
    throw new OwnerLaneEndToEndCanaryError("Unsupported canary input contract version.");
  }
  const recordedAt = requireString(input.recorded_at, "recorded_at");
  if (Number.isNaN(Date.parse(recordedAt))) throw new OwnerLaneEndToEndCanaryError("recorded_at must be an ISO date-time.");
  if (!Array.isArray(input.tasks) || input.tasks.length !== REQUIRED_PROJECTS.size) {
    throw new OwnerLaneEndToEndCanaryError("Canary requires exactly one Atlas, one Mazer, and one Fitness task.");
  }
  const tasks = (await Promise.all(input.tasks.map((task) => resolveNativeTaskEvidence(task, { codexHome })))).map(assertTask);
  const projectIds = new Set(tasks.map((task) => task.project_id));
  if (projectIds.size !== REQUIRED_PROJECTS.size || [...REQUIRED_PROJECTS.keys()].some((id) => !projectIds.has(id))) {
    throw new OwnerLaneEndToEndCanaryError("Canary project set is incomplete or duplicated.");
  }
  if (new Set(tasks.map((task) => task.thread_id)).size !== tasks.length) {
    throw new OwnerLaneEndToEndCanaryError("Each project canary requires a distinct native task identity.");
  }
  const boardReadback = await resolveBoardReadbackEvidence(input.board_readback_source, { atlasRoot, recordedAt });
  assertBoardReadback(boardReadback);
  const authorityDrift = tasks.some((task) => task.changed_paths.length > 0
    || task.authority_actions.length > 0 || task.blockers.length > 0)
    || boardReadback.external_mutation !== "not_performed";
  if (authorityDrift) throw new OwnerLaneEndToEndCanaryError("Resolved native evidence contains authority drift.");

  const receipts = [];
  for (const task of tasks) {
    receipts.push(await correlateNativeTask({
      job: jobEnvelope(task, recordedAt),
      taskResult: nativeTaskResult(task, recordedAt),
      contextPacket: contextPacket(task, recordedAt),
      evidenceBundle: evidenceBundle(task, recordedAt),
      workerLease: workerLease(task, recordedAt),
    }));
  }

  const mazerTask = tasks.find((task) => task.project_id === "mazer");
  const mazerReceipt = receipts.find((receipt) => receipt.project_id === "mazer");
  const mazerJob = jobEnvelope(mazerTask, recordedAt);
  const card = {
    contract_version: "atlas.card-record.v2",
    card_id: mazerTask.card_id,
    project_id: "mazer",
    board_id: boardReadback.board_id,
    title: mazerTask.card_title,
    description: "Existing Mazer card used for read-only unit-10 correlation proof.",
    card_type: "governance",
    lifecycle: mazerTask.card_state,
    priority: "medium",
    owner: "Mazer",
    dependencies: [],
    board_version: boardReadback.observed_board_version,
    updated_at: recordedAt,
    source_ref: boardReadback.receipt_id,
    extensions: { external_mutation: "not_performed" },
  };
  const boardEvent = await buildBoardEvent({
    job: mazerJob,
    receipt: mazerReceipt,
    card,
    eventType: "readback",
    occurredAt: recordedAt,
    fromState: card.lifecycle,
    toState: card.lifecycle,
    reason: "unit-10 read-only correlation proof",
    status: "verified",
    observedVersion: boardReadback.observed_board_version,
    readbackAt: recordedAt,
    readbackReceiptRef: boardReadback.receipt_id,
  });

  const identity = {
    recorded_at: recordedAt,
    tasks: receipts.map((receipt) => ({
      project_id: receipt.project_id,
      job_id: receipt.job_id,
      receipt_id: receipt.receipt_id,
      thread_id: receipt.correlations.thread_id,
      turn_id: receipt.correlations.turn_id,
      session_digest: tasks.find((task) => task.project_id === receipt.project_id).native_evidence.session_digest,
      initial_command_digests: tasks.find((task) => task.project_id === receipt.project_id)
        .native_evidence.initial_turn.commands.map((command) => command.output_digest),
      recovery_command_digests: tasks.find((task) => task.project_id === receipt.project_id)
        .native_evidence.recovery_turn.commands.map((command) => command.output_digest),
    })),
    board_event_id: boardEvent.event_id,
    board_readback_receipt_id: boardReadback.receipt_id,
    board_readback_source_digest: boardReadback.source_digest,
  };
  const receiptId = `aec_${crypto.createHash("sha256").update(JSON.stringify(identity)).digest("hex").slice(0, 32)}`;
  return {
    contract_version: "atlas.owner-lane-e2e-canary-receipt.v1",
    receipt_id: receiptId,
    recorded_at: recordedAt,
    status: "succeeded",
    completed_projects: [...REQUIRED_PROJECTS.keys()],
    recovery_proven: true,
    authority_drift: authorityDrift,
    external_mutation: "not_performed",
    production_deploy: false,
    execution_receipts: receipts,
    board_event: boardEvent,
    board_readback: boardReadback,
    source_evidence: {
      tasks: tasks.map((task) => ({
        project_id: task.project_id,
        thread_id: task.thread_id,
        initial_turn_id: task.initial_turn_id,
        recovery_turn_id: task.recovery_turn_id,
        session_ref: task.native_evidence.session_ref,
        session_digest: task.native_evidence.session_digest,
        initial_commands: task.native_evidence.initial_turn.commands,
        recovery_commands: task.native_evidence.recovery_turn.commands,
      })),
      board: {
        artifact_ref: boardReadback.source_artifact_ref,
        artifact_digest: boardReadback.source_digest,
        receipt_id: boardReadback.receipt_id,
      },
    },
  };
}

export async function run(argv) {
  const options = parseArguments(argv);
  const inputPath = safePath(options.input);
  const outputPath = safePath(options.output, true);
  const input = JSON.parse(await fs.readFile(inputPath.resolved, "utf8"));
  const receipt = await buildOwnerLaneEndToEndCanary(input);
  await fs.mkdir(path.dirname(outputPath.resolved), { recursive: true });
  await fs.writeFile(outputPath.resolved, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  return {
    status: receipt.status,
    receipt_id: receipt.receipt_id,
    output: outputPath.relative,
    completed_projects: receipt.completed_projects,
    recovery_proven: receipt.recovery_proven,
    authority_drift: receipt.authority_drift,
    board_event_id: receipt.board_event.event_id,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(await run(process.argv.slice(2)), null, 2));
  } catch (error) {
    console.error(JSON.stringify({ status: "blocked", error: error.message }, null, 2));
    process.exitCode = 1;
  }
}
