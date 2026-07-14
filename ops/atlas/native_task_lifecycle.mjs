import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadKnownSchema, validateJsonSchema } from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const TERMINAL = new Set(["succeeded", "failed", "blocked", "cancelled"]);
const TRANSITIONS = Object.freeze({
  admit: { from: [null], to: "admitted" },
  start: { from: ["admitted"], to: "running" },
  "await-review": { from: ["running"], to: "awaiting-review" },
  succeed: { from: ["running", "awaiting-review"], to: "succeeded" },
  fail: { from: ["running", "awaiting-review"], to: "failed" },
  block: { from: ["running", "awaiting-review"], to: "blocked" },
  cancel: { from: ["admitted", "running", "awaiting-review"], to: "cancelled" },
  retry: { from: ["failed", "blocked", "cancelled"], to: "admitted" },
  replay: { from: ["succeeded", "failed", "blocked", "cancelled"], to: "admitted" },
  archive: { from: ["succeeded", "failed", "blocked", "cancelled"], to: "archived" },
});

export class NativeTaskLifecycleError extends Error {}

function parseArguments(argv) {
  const options = { previous: null, receiptId: null, reason: null, output: null };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const match = argument.match(/^--(job-id|component-id|thread-id|turn-id|action|occurred-at|previous|receipt-id|reason|output)=(.*)$/);
    if (match) {
      options[match[1].replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = match[2] || null;
      continue;
    }
    if (argument.startsWith("--")) {
      const key = argument.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        throw new NativeTaskLifecycleError(`${argument} requires a value.`);
      }
      options[key] = value;
      index += 1;
      continue;
    }
    throw new NativeTaskLifecycleError(`Unsupported argument: ${argument}`);
  }
  for (const key of ["jobId", "componentId", "threadId", "turnId", "action", "occurredAt", "output"]) {
    if (!options[key]) {
      throw new NativeTaskLifecycleError(`Missing required argument: ${key}.`);
    }
  }
  return options;
}

function rootRelative(inputPath) {
  const resolved = path.resolve(ROOT, inputPath);
  const relative = path.relative(ROOT, resolved).replaceAll("\\", "/");
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new NativeTaskLifecycleError("Path must resolve inside the Atlas root.");
  }
  return { resolved, relative };
}

function safeInput(inputPath) {
  const candidate = rootRelative(inputPath);
  const lower = candidate.relative.toLowerCase().split("/");
  if (lower.includes("secrets") || lower.some((segment) => segment === ".env" || segment.startsWith(".env."))) {
    throw new NativeTaskLifecycleError(`Sensitive input path is forbidden: ${candidate.relative}`);
  }
  return candidate;
}

function safeOutput(outputPath) {
  const candidate = rootRelative(outputPath);
  if (!candidate.relative.startsWith("runtime/atlas/native-task-lifecycle/") && !candidate.relative.startsWith("tmp/")) {
    throw new NativeTaskLifecycleError("Output must be under runtime/atlas/native-task-lifecycle/ or tmp/.");
  }
  return candidate;
}

async function validateEvent(event, label = "Lifecycle event") {
  const schema = await loadKnownSchema("atlas.event.v1");
  if (!schema.ok) {
    throw new NativeTaskLifecycleError(`Event schema unavailable: ${schema.error}`);
  }
  const errors = validateJsonSchema(event, schema.schema);
  if (errors.length > 0) {
    throw new NativeTaskLifecycleError(`${label} failed atlas.event.v1: ${errors.join(" ")}`);
  }
}

async function loadPrevious(previousPath) {
  if (!previousPath) return null;
  const candidate = safeInput(previousPath);
  let payload;
  try {
    payload = JSON.parse(await fs.readFile(candidate.resolved, "utf8"));
  } catch (error) {
    throw new NativeTaskLifecycleError(`Previous event is not readable JSON: ${error.message}`);
  }
  await validateEvent(payload, "Previous event");
  if (payload.event_type !== `native-task.lifecycle.${payload.payload?.to_state}`) {
    throw new NativeTaskLifecycleError("Previous event is not a coherent native lifecycle event.");
  }
  return payload;
}

export async function buildLifecycleEvent({
  jobId,
  componentId,
  threadId,
  turnId,
  action,
  occurredAt,
  previousEvent = null,
  receiptId = null,
  reason = null,
}) {
  const transition = TRANSITIONS[action];
  if (!transition) {
    throw new NativeTaskLifecycleError(`Unsupported lifecycle action: ${action}`);
  }
  if (Number.isNaN(Date.parse(occurredAt))) {
    throw new NativeTaskLifecycleError("occurredAt must be an ISO date-time.");
  }
  const fromState = previousEvent?.payload?.to_state ?? null;
  if (!transition.from.includes(fromState)) {
    throw new NativeTaskLifecycleError(`Invalid lifecycle transition: ${fromState ?? "null"} --${action}--> ${transition.to}.`);
  }
  if (previousEvent) {
    if (
      previousEvent.payload.job_id !== jobId
      || previousEvent.task?.task_id !== threadId
      || previousEvent.repo_id !== componentId
    ) {
      throw new NativeTaskLifecycleError("Previous lifecycle event identity does not match the current job, thread, and component.");
    }
    if (Date.parse(occurredAt) < Date.parse(previousEvent.occurred_at)) {
      throw new NativeTaskLifecycleError("Lifecycle event time cannot move backward.");
    }
  }
  if (action === "archive" && (!receiptId || receiptId.trim() === "")) {
    throw new NativeTaskLifecycleError("Archive requires a durable receipt_id.");
  }
  const previousAttempt = previousEvent?.payload?.attempt ?? 0;
  const attempt = action === "admit" ? 1 : ["retry", "replay"].includes(action) ? previousAttempt + 1 : previousAttempt;
  const sequence = (previousEvent?.payload?.sequence ?? 0) + 1;
  const previousEventId = previousEvent?.event_id ?? null;
  const seed = `${jobId}\n${threadId}\n${turnId}\n${sequence}\n${action}\n${previousEventId ?? ""}`;
  const eventId = `atl_${crypto.createHash("sha256").update(seed).digest("hex").slice(0, 24)}`;
  const event = {
    contract_version: "atlas.event.v1",
    event_type: `native-task.lifecycle.${transition.to}`,
    event_id: eventId,
    occurred_at: occurredAt,
    repo_id: componentId,
    app_id: "atlas-control",
    environment: "local",
    producer: { kind: "wrapper", name: "atlas-native-task-lifecycle", version: "1", host: "local" },
    task: {
      task_id: threadId,
      task_name: jobId,
      scope_paths: [],
      repo_ids: [componentId],
      mutation_mode: "coordination-only",
    },
    trace: { correlation_id: jobId, trace_id: null, span_id: null },
    subject: { kind: "atlas-job", id: jobId, path: null },
    payload: {
      lifecycle_version: "atlas.native-task-lifecycle.v1",
      job_id: jobId,
      thread_id: threadId,
      turn_id: turnId,
      sequence,
      attempt,
      action,
      from_state: fromState,
      to_state: transition.to,
      previous_event_id: previousEventId,
      receipt_id: receiptId,
      replay_of: action === "replay" ? previousEventId : null,
      reason,
      terminal: TERMINAL.has(transition.to) || transition.to === "archived",
    },
    links: receiptId ? [{ rel: "execution-receipt", href: receiptId }] : [],
  };
  await validateEvent(event);
  return event;
}

export async function run(argv) {
  const options = parseArguments(argv);
  const previousEvent = await loadPrevious(options.previous);
  const event = await buildLifecycleEvent({ ...options, previousEvent });
  const output = safeOutput(options.output);
  await fs.mkdir(path.dirname(output.resolved), { recursive: true });
  await fs.writeFile(output.resolved, `${JSON.stringify(event, null, 2)}\n`, "utf8");
  return {
    status: "written",
    output: output.relative,
    event_id: event.event_id,
    action: event.payload.action,
    from_state: event.payload.from_state,
    to_state: event.payload.to_state,
    attempt: event.payload.attempt,
    sequence: event.payload.sequence,
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
