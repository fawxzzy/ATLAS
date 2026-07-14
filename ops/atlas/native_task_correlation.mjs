import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import {
  loadKnownSchema,
  validateJsonSchema,
} from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUTPUT_PREFIXES = ["runtime/atlas/native-task-correlations/", "tmp/"];
const TERMINAL_STATUS = new Map([
  ["completed", "succeeded"],
  ["failed", "failed"],
  ["blocked", "blocked"],
  ["cancelled", "cancelled"],
  ["awaiting-review", "awaiting-review"],
  ["partial", "partial"],
]);

export class NativeTaskCorrelationError extends Error {}

function parseArguments(argv) {
  const options = { dryRun: false, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    if (argument === "--json") {
      options.json = true;
      continue;
    }
    const match = argument.match(/^--(job|task-result|context|evidence|output)=(.+)$/);
    if (match) {
      options[match[1] === "task-result" ? "taskResult" : match[1]] = match[2];
      continue;
    }
    if (["--job", "--task-result", "--context", "--evidence", "--output"].includes(argument)) {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        throw new NativeTaskCorrelationError(`${argument} requires a value.`);
      }
      options[argument === "--task-result" ? "taskResult" : argument.slice(2)] = value;
      index += 1;
      continue;
    }
    throw new NativeTaskCorrelationError(`Unsupported argument: ${argument}`);
  }
  for (const key of ["job", "taskResult", "context", "evidence", "output"]) {
    if (!options[key]) {
      throw new NativeTaskCorrelationError(`Missing required argument: ${key}.`);
    }
  }
  return options;
}

function rootRelative(inputPath) {
  const resolved = path.resolve(ROOT, inputPath);
  const relative = path.relative(ROOT, resolved).replaceAll("\\", "/");
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new NativeTaskCorrelationError("Path must resolve inside the Atlas root.");
  }
  return { resolved, relative };
}

function assertSafeInput(inputPath) {
  const candidate = rootRelative(inputPath);
  const segments = candidate.relative.toLowerCase().split("/");
  if (segments.includes("secrets") || segments.some((segment) => segment === ".env" || segment.startsWith(".env."))) {
    throw new NativeTaskCorrelationError(`Sensitive input path is forbidden: ${candidate.relative}`);
  }
  return candidate;
}

function assertSafeOutput(outputPath) {
  const candidate = rootRelative(outputPath);
  if (!OUTPUT_PREFIXES.some((prefix) => candidate.relative.startsWith(prefix))) {
    throw new NativeTaskCorrelationError("Output must be under runtime/atlas/native-task-correlations/ or tmp/.");
  }
  return candidate;
}

async function readJson(filePath, label) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (error) {
    throw new NativeTaskCorrelationError(`${label} is not readable JSON: ${error.message}`);
  }
}

async function validateContract(payload, contractVersion, label) {
  const loaded = await loadKnownSchema(contractVersion);
  if (!loaded.ok) {
    throw new NativeTaskCorrelationError(`${label} schema is unavailable: ${loaded.error}`);
  }
  const errors = validateJsonSchema(payload, loaded.schema);
  if (errors.length > 0) {
    throw new NativeTaskCorrelationError(`${label} failed ${contractVersion}: ${errors.join(" ")}`);
  }
}

function requireString(payload, key) {
  const value = payload[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new NativeTaskCorrelationError(`Native task result requires non-empty ${key}.`);
  }
  return value;
}

function stringArray(payload, key) {
  const value = payload[key] ?? [];
  if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string" || entry.trim() === "")) {
    throw new NativeTaskCorrelationError(`${key} must be an array of non-empty strings.`);
  }
  return value;
}

function nullableString(payload, key) {
  const value = payload[key] ?? null;
  if (value !== null && (typeof value !== "string" || value.trim() === "")) {
    throw new NativeTaskCorrelationError(`${key} must be null or a non-empty string.`);
  }
  return value;
}

function runtimeEffective(taskResult) {
  const supplied = taskResult.runtime_effective;
  if (supplied === undefined) {
    return {
      model: "unavailable",
      reasoning: "unavailable",
      speed: "unavailable",
      permissions: "unavailable",
      approval_policy: "unavailable",
    };
  }
  if (!supplied || typeof supplied !== "object" || Array.isArray(supplied)) {
    throw new NativeTaskCorrelationError("runtime_effective must be an object when present.");
  }
  return Object.fromEntries(
    ["model", "reasoning", "speed", "permissions", "approval_policy"].map((key) => [key, requireString(supplied, key)]),
  );
}

function contentDigest(payload) {
  return `sha256:${crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex")}`;
}

function assertMatchingIdentity(payload, job, label) {
  if (payload.job_id !== job.job_id) {
    throw new NativeTaskCorrelationError(`${label} job correlation mismatch: ${job.job_id} != ${payload.job_id}.`);
  }
  const componentId = payload.component_id ?? payload.environment?.component_id;
  if (componentId !== job.component_id) {
    throw new NativeTaskCorrelationError(
      `${label} component correlation mismatch: ${job.component_id} != ${componentId}.`,
    );
  }
}

function normalizeVerification(taskResult) {
  const records = taskResult.verification ?? [];
  if (!Array.isArray(records)) {
    throw new NativeTaskCorrelationError("verification must be an array when present.");
  }
  return records.map((record) => {
    if (!record || typeof record !== "object" || Array.isArray(record)) {
      throw new NativeTaskCorrelationError("verification entries must be objects.");
    }
    const status = requireString(record, "status");
    if (!new Set(["passed", "failed", "skipped", "blocked"]).has(status)) {
      throw new NativeTaskCorrelationError(`Unsupported verification status: ${status}`);
    }
    return {
      command: requireString(record, "command"),
      status,
      evidence_refs: stringArray(record, "evidence_refs"),
    };
  });
}

export async function correlateNativeTask({ job, taskResult, contextPacket, evidenceBundle }) {
  await validateContract(job, "atlas.job-envelope.v2", "Job envelope");
  await validateContract(contextPacket, "atlas.context-packet.v2", "Context packet");
  await validateContract(evidenceBundle, "atlas.evidence-bundle.v2", "Evidence bundle");
  assertMatchingIdentity(contextPacket, job, "Context packet");
  assertMatchingIdentity(evidenceBundle, job, "Evidence bundle");
  if (!taskResult || typeof taskResult !== "object" || Array.isArray(taskResult)) {
    throw new NativeTaskCorrelationError("Native task result must be an object.");
  }
  const taskJobId = requireString(taskResult, "job_id");
  if (taskJobId !== job.job_id) {
    throw new NativeTaskCorrelationError(`Job correlation mismatch: ${job.job_id} != ${taskJobId}.`);
  }
  const terminalStatus = requireString(taskResult, "terminal_status");
  if (!TERMINAL_STATUS.has(terminalStatus)) {
    throw new NativeTaskCorrelationError(`Unsupported terminal_status: ${terminalStatus}`);
  }
  const threadId = requireString(taskResult, "thread_id");
  const turnId = requireString(taskResult, "turn_id");
  const recordedAt = requireString(taskResult, "recorded_at");
  if (Number.isNaN(Date.parse(recordedAt))) {
    throw new NativeTaskCorrelationError("recorded_at must be an ISO date-time.");
  }
  const receiptSeed = `${job.job_id}\n${threadId}\n${turnId}\n${terminalStatus}`;
  const receiptId = `atr_${crypto.createHash("sha256").update(receiptSeed).digest("hex").slice(0, 24)}`;
  const finalResponse = requireString(taskResult, "final_response");

  const evidenceRefs = [
    ...stringArray(taskResult, "evidence_refs"),
    ...evidenceBundle.evidence.map((item) => item.ref),
  ].filter((value, index, values) => values.indexOf(value) === index);
  const receipt = {
    contract_version: "atlas.execution-receipt.v2",
    receipt_id: receiptId,
    job_id: job.job_id,
    recorded_at: recordedAt,
    status: TERMINAL_STATUS.get(terminalStatus),
    component_id: job.component_id,
    project_id: job.project_id,
    runtime_effective: runtimeEffective(taskResult),
    changed_paths: stringArray(taskResult, "changed_paths"),
    commits: stringArray(taskResult, "commits"),
    verification: normalizeVerification(taskResult),
    evidence_refs: evidenceRefs,
    blockers: stringArray(taskResult, "blockers"),
    follow_up: stringArray(taskResult, "follow_up"),
    correlations: {
      card_id: job.correlations.card_id,
      thread_id: threadId,
      turn_id: turnId,
      branch: nullableString(taskResult, "branch"),
      worktree: nullableString(taskResult, "worktree"),
    },
    authority_actions: stringArray(taskResult, "authority_actions"),
    summary: finalResponse,
    extensions: {
      native_task_result_version: "atlas.native-task-result.v1",
      runtime_requested: job.runtime,
      runtime_policy_observed: taskResult.runtime_effective !== undefined,
      task_result_status: terminalStatus,
      context_binding: {
        context_id: contextPacket.context_id,
        digest: contentDigest(contextPacket),
        source_count: contextPacket.sources.length,
      },
      evidence_binding: {
        bundle_id: evidenceBundle.bundle_id,
        digest: contentDigest(evidenceBundle),
        item_count: evidenceBundle.evidence.length,
        classifications: evidenceBundle.classifications,
      },
    },
  };
  await validateContract(receipt, "atlas.execution-receipt.v2", "Execution receipt");
  return receipt;
}

export async function run(argv) {
  const options = parseArguments(argv);
  const jobPath = assertSafeInput(options.job);
  const taskResultPath = assertSafeInput(options.taskResult);
  const contextPath = assertSafeInput(options.context);
  const evidencePath = assertSafeInput(options.evidence);
  const outputPath = assertSafeOutput(options.output);
  const job = await readJson(jobPath.resolved, "Job envelope");
  const taskResult = await readJson(taskResultPath.resolved, "Native task result");
  const contextPacket = await readJson(contextPath.resolved, "Context packet");
  const evidenceBundle = await readJson(evidencePath.resolved, "Evidence bundle");
  const receipt = await correlateNativeTask({ job, taskResult, contextPacket, evidenceBundle });
  if (!options.dryRun) {
    await fs.mkdir(path.dirname(outputPath.resolved), { recursive: true });
    await fs.writeFile(outputPath.resolved, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  }
  return {
    status: options.dryRun ? "valid_dry_run" : "written",
    output: outputPath.relative,
    receipt_id: receipt.receipt_id,
    job_id: receipt.job_id,
    thread_id: receipt.correlations.thread_id,
    turn_id: receipt.correlations.turn_id,
    runtime_policy_observed: receipt.extensions.runtime_policy_observed,
    context_id: receipt.extensions.context_binding.context_id,
    evidence_bundle_id: receipt.extensions.evidence_binding.bundle_id,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const result = await run(process.argv.slice(2));
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error(JSON.stringify({ status: "blocked", error: error.message }, null, 2));
    process.exitCode = 1;
  }
}
