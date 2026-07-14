import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadKnownSchema, validateJsonSchema } from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const READBACK_STATUSES = new Set(["applied", "duplicate", "conflict", "failed", "verified"]);

export class NativeBoardCorrelationError extends Error {}

function canonicalDigest(value) {
  return `sha256:${crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

function rootRelative(inputPath) {
  const resolved = path.resolve(ROOT, inputPath);
  const relative = path.relative(ROOT, resolved).replaceAll("\\", "/");
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new NativeBoardCorrelationError("Path must resolve inside the Atlas root.");
  }
  return { resolved, relative };
}

function safeInput(inputPath) {
  const candidate = rootRelative(inputPath);
  const segments = candidate.relative.toLowerCase().split("/");
  if (segments.includes("secrets") || segments.some((segment) => segment === ".env" || segment.startsWith(".env."))) {
    throw new NativeBoardCorrelationError(`Sensitive input path is forbidden: ${candidate.relative}`);
  }
  return candidate;
}

function safeOutput(outputPath) {
  const candidate = rootRelative(outputPath);
  if (!candidate.relative.startsWith("runtime/atlas/native-board-correlations/") && !candidate.relative.startsWith("tmp/")) {
    throw new NativeBoardCorrelationError("Output must be under runtime/atlas/native-board-correlations/ or tmp/.");
  }
  return candidate;
}

async function validateArtifact(artifact, schemaId, label) {
  const schema = await loadKnownSchema(schemaId);
  if (!schema.ok) throw new NativeBoardCorrelationError(`${label} schema unavailable: ${schema.error}`);
  const errors = validateJsonSchema(artifact, schema.schema);
  if (errors.length > 0) throw new NativeBoardCorrelationError(`${label} failed ${schemaId}: ${errors.join(" ")}`);
}

async function loadArtifact(inputPath, schemaId, label) {
  const candidate = safeInput(inputPath);
  let artifact;
  try {
    artifact = JSON.parse(await fs.readFile(candidate.resolved, "utf8"));
  } catch (error) {
    throw new NativeBoardCorrelationError(`${label} is not readable JSON: ${error.message}`);
  }
  await validateArtifact(artifact, schemaId, label);
  return artifact;
}

export async function buildBoardEvent({
  job,
  receipt,
  card,
  eventType,
  occurredAt,
  fromState,
  toState,
  reason,
  status = "pending",
  expectedVersion = card?.board_version,
  observedVersion = null,
  readbackAt = null,
  readbackReceiptRef = null,
  errorCode = null,
}) {
  await validateArtifact(job, "atlas.job-envelope.v2", "JobEnvelope");
  await validateArtifact(receipt, "atlas.execution-receipt.v2", "ExecutionReceipt");
  await validateArtifact(card, "atlas.card-record.v2", "CardRecord");
  if (job.job_id !== receipt.job_id) throw new NativeBoardCorrelationError("ExecutionReceipt job identity does not match JobEnvelope.");
  if (job.project_id !== receipt.project_id || job.project_id !== card.project_id) {
    throw new NativeBoardCorrelationError("Project identity does not match across job, receipt, and card.");
  }
  if (job.correlations.card_id !== card.card_id || receipt.correlations.card_id !== card.card_id) {
    throw new NativeBoardCorrelationError("Card identity does not match across job, receipt, and card.");
  }
  if (receipt.status !== "succeeded") throw new NativeBoardCorrelationError("Board correlation requires a succeeded ExecutionReceipt.");
  if (expectedVersion !== card.board_version) throw new NativeBoardCorrelationError("Board event expected_version must match CardRecord board_version.");
  if (fromState !== card.lifecycle) throw new NativeBoardCorrelationError("Board event from state must match CardRecord lifecycle.");
  if (Number.isNaN(Date.parse(occurredAt))) throw new NativeBoardCorrelationError("occurredAt must be an ISO date-time.");
  if (status === "pending") {
    if (observedVersion !== null || readbackAt !== null || readbackReceiptRef !== null || errorCode !== null) {
      throw new NativeBoardCorrelationError("Pending board intent cannot claim readback or error result fields.");
    }
  } else if (READBACK_STATUSES.has(status)) {
    if (!Number.isInteger(observedVersion) || !readbackAt || Number.isNaN(Date.parse(readbackAt)) || !readbackReceiptRef) {
      throw new NativeBoardCorrelationError("Observed board result requires version, readback time, and receipt reference.");
    }
    if (["conflict", "failed"].includes(status) && !errorCode) {
      throw new NativeBoardCorrelationError("Conflict or failure board result requires error_code.");
    }
  } else {
    throw new NativeBoardCorrelationError(`Unsupported board result status: ${status}`);
  }

  const identity = {
    job_id: job.job_id,
    card_id: card.card_id,
    board_id: card.board_id,
    expected_version: expectedVersion,
    from: fromState,
    to: toState,
    reason,
  };
  const idempotencyKey = `abk_${crypto.createHash("sha256").update(JSON.stringify(identity)).digest("hex").slice(0, 32)}`;
  const eventId = `abe_${crypto.createHash("sha256").update(`${idempotencyKey}\n${eventType}\n${status}\n${occurredAt}`).digest("hex").slice(0, 32)}`;
  const event = {
    contract_version: "atlas.board-event.v2",
    event_id: eventId,
    idempotency_key: idempotencyKey,
    job_id: job.job_id,
    card_id: card.card_id,
    board_id: card.board_id,
    event_type: eventType,
    occurred_at: occurredAt,
    expected_version: expectedVersion,
    intent: { from: fromState, to: toState, reason },
    result: {
      status,
      observed_version: observedVersion,
      readback_at: readbackAt,
      receipt_ref: readbackReceiptRef,
      error_code: errorCode,
    },
    extensions: {
      writer_authority: "discordos",
      external_mutation: status === "pending" ? "not_performed" : "observed_only",
      execution_receipt_id: receipt.receipt_id,
      native_task_id: receipt.correlations.thread_id,
      native_turn_id: receipt.correlations.turn_id,
      card_digest: canonicalDigest(card),
    },
  };
  await validateArtifact(event, "atlas.board-event.v2", "BoardEvent");
  return event;
}

function parseArguments(argv) {
  const options = { status: "pending", observedVersion: null, readbackAt: null, readbackReceiptRef: null, errorCode: null };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) throw new NativeBoardCorrelationError(`Unsupported argument: ${argument}`);
    const key = argument.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new NativeBoardCorrelationError(`${argument} requires a value.`);
    options[key] = value;
    index += 1;
  }
  for (const key of ["job", "receipt", "card", "eventType", "occurredAt", "fromState", "toState", "reason", "output"]) {
    if (!options[key]) throw new NativeBoardCorrelationError(`Missing required argument: ${key}.`);
  }
  if (options.expectedVersion !== undefined) options.expectedVersion = Number.parseInt(options.expectedVersion, 10);
  if (options.observedVersion !== null) options.observedVersion = Number.parseInt(options.observedVersion, 10);
  return options;
}

export async function run(argv) {
  const options = parseArguments(argv);
  const [job, receipt, card] = await Promise.all([
    loadArtifact(options.job, "atlas.job-envelope.v2", "JobEnvelope"),
    loadArtifact(options.receipt, "atlas.execution-receipt.v2", "ExecutionReceipt"),
    loadArtifact(options.card, "atlas.card-record.v2", "CardRecord"),
  ]);
  const event = await buildBoardEvent({ ...options, job, receipt, card });
  const output = safeOutput(options.output);
  await fs.mkdir(path.dirname(output.resolved), { recursive: true });
  await fs.writeFile(output.resolved, `${JSON.stringify(event, null, 2)}\n`, "utf8");
  return { status: "written", output: output.relative, event_id: event.event_id, idempotency_key: event.idempotency_key, result: event.result.status };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(await run(process.argv.slice(2)), null, 2));
  } catch (error) {
    console.error(JSON.stringify({ status: "blocked", error: error.message }, null, 2));
    process.exitCode = 1;
  }
}
