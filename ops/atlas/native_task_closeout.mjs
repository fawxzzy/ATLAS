import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadKnownSchema, validateJsonSchema } from "../../packages/atlas-contracts/scripts/lib/validate-json-schema.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

export class NativeTaskCloseoutError extends Error {}

function digestId(prefix, value) {
  return `${prefix}_${crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex").slice(0, 24)}`;
}

function rootRelative(inputPath) {
  const resolved = path.resolve(ROOT, inputPath);
  const relative = path.relative(ROOT, resolved).replaceAll("\\", "/");
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new NativeTaskCloseoutError("Path must resolve inside the Atlas root.");
  }
  return { resolved, relative };
}

function safeInput(inputPath) {
  const candidate = rootRelative(inputPath);
  const segments = candidate.relative.toLowerCase().split("/");
  if (segments.includes("secrets") || segments.some((segment) => segment === ".env" || segment.startsWith(".env."))) {
    throw new NativeTaskCloseoutError(`Sensitive input path is forbidden: ${candidate.relative}`);
  }
  return candidate;
}

function safeOutputDirectory(outputPath) {
  const candidate = rootRelative(outputPath);
  if (!candidate.relative.startsWith("runtime/atlas/native-task-closeouts/") && !candidate.relative.startsWith("tmp/")) {
    throw new NativeTaskCloseoutError("Output must be under runtime/atlas/native-task-closeouts/ or tmp/.");
  }
  return candidate;
}

async function validateArtifact(artifact, schemaId, label) {
  const schema = await loadKnownSchema(schemaId);
  if (!schema.ok) throw new NativeTaskCloseoutError(`${label} schema unavailable: ${schema.error}`);
  const errors = validateJsonSchema(artifact, schema.schema);
  if (errors.length > 0) throw new NativeTaskCloseoutError(`${label} failed ${schemaId}: ${errors.join(" ")}`);
}

async function loadReceipt(inputPath) {
  const candidate = safeInput(inputPath);
  let receipt;
  try {
    receipt = JSON.parse(await fs.readFile(candidate.resolved, "utf8"));
  } catch (error) {
    throw new NativeTaskCloseoutError(`ExecutionReceipt is not readable JSON: ${error.message}`);
  }
  await validateArtifact(receipt, "atlas.execution-receipt.v2", "ExecutionReceipt");
  return receipt;
}

export async function buildCloseout({
  receipt,
  markerId,
  markerScope,
  numerator,
  denominator,
  previousPercentage,
  measuredAt,
  validUntil = null,
  transitionReason,
  rollupPolicy = "independent",
  evidenceRefs = [],
  knowledgeKind,
  knowledgeName,
  knowledgeStatement,
  knowledgeScope,
  suggestedDestination,
  provenanceRefs = [],
}) {
  await validateArtifact(receipt, "atlas.execution-receipt.v2", "ExecutionReceipt");
  if (receipt.status !== "succeeded") throw new NativeTaskCloseoutError("Closeout requires a succeeded ExecutionReceipt.");
  if (!Number.isInteger(numerator) || !Number.isInteger(denominator) || denominator < 1 || numerator < 0 || numerator > denominator) {
    throw new NativeTaskCloseoutError("Marker numerator and denominator must be bounded integers.");
  }
  if (previousPercentage !== null && (!Number.isFinite(previousPercentage) || previousPercentage < 0 || previousPercentage > 100)) {
    throw new NativeTaskCloseoutError("previousPercentage must be null or between 0 and 100.");
  }
  if (Number.isNaN(Date.parse(measuredAt))) throw new NativeTaskCloseoutError("measuredAt must be an ISO date-time.");
  if (validUntil && (Number.isNaN(Date.parse(validUntil)) || Date.parse(validUntil) < Date.parse(measuredAt))) {
    throw new NativeTaskCloseoutError("validUntil must be null or no earlier than measuredAt.");
  }
  const percentage = (numerator / denominator) * 100;
  const allEvidenceRefs = [...new Set([`receipt:${receipt.receipt_id}`, ...receipt.evidence_refs, ...evidenceRefs])];
  const markerEvidence = {
    contract_version: "atlas.marker-evidence.v2",
    marker_id: markerId,
    scope: markerScope,
    measured_at: measuredAt,
    numerator,
    denominator,
    percentage,
    evidence_refs: allEvidenceRefs,
    freshness: { status: "current", valid_until: validUntil },
    transition: { previous_percentage: previousPercentage, current_percentage: percentage, reason: transitionReason },
    rollup_policy: rollupPolicy,
    extensions: { job_id: receipt.job_id, execution_receipt_id: receipt.receipt_id },
  };
  const provenance = [
    { source_type: "receipt", ref: receipt.receipt_id, classification: "verified" },
    ...provenanceRefs.map((ref) => ({ source_type: "repository", ref, classification: "verified" })),
  ];
  const candidateIdentity = { kind: knowledgeKind, name: knowledgeName, statement: knowledgeStatement, scope: knowledgeScope, provenance };
  const knowledgeCandidate = {
    contract_version: "atlas.knowledge-candidate.v2",
    candidate_id: digestId("akc", candidateIdentity),
    kind: knowledgeKind,
    name: knowledgeName,
    statement: knowledgeStatement,
    scope: knowledgeScope,
    provenance,
    review: { status: "candidate", reviewer: null, reviewed_at: null, decision_note: null },
    suggested_destination: suggestedDestination,
    created_at: measuredAt,
    extensions: { job_id: receipt.job_id, execution_receipt_id: receipt.receipt_id, marker_id: markerId },
  };
  await validateArtifact(markerEvidence, "atlas.marker-evidence.v2", "MarkerEvidence");
  await validateArtifact(knowledgeCandidate, "atlas.knowledge-candidate.v2", "KnowledgeCandidate");
  return { markerEvidence, knowledgeCandidate };
}

function parseArguments(argv) {
  const options = { validUntil: null, rollupPolicy: "independent", evidenceRefs: [], provenanceRefs: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) throw new NativeTaskCloseoutError(`Unsupported argument: ${argument}`);
    const key = argument.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new NativeTaskCloseoutError(`${argument} requires a value.`);
    if (key === "evidenceRef") options.evidenceRefs.push(value);
    else if (key === "provenanceRef") options.provenanceRefs.push(value);
    else options[key] = value;
    index += 1;
  }
  for (const key of ["receipt", "markerId", "markerScope", "numerator", "denominator", "previousPercentage", "measuredAt", "transitionReason", "knowledgeKind", "knowledgeName", "knowledgeStatement", "knowledgeScope", "suggestedDestination", "outputDir"]) {
    if (options[key] === undefined || options[key] === null || options[key] === "") throw new NativeTaskCloseoutError(`Missing required argument: ${key}.`);
  }
  options.numerator = Number.parseInt(options.numerator, 10);
  options.denominator = Number.parseInt(options.denominator, 10);
  options.previousPercentage = options.previousPercentage === "null" ? null : Number.parseFloat(options.previousPercentage);
  return options;
}

export async function run(argv) {
  const options = parseArguments(argv);
  const receipt = await loadReceipt(options.receipt);
  const closeout = await buildCloseout({ ...options, receipt });
  const output = safeOutputDirectory(options.outputDir);
  await fs.mkdir(output.resolved, { recursive: true });
  const markerPath = path.join(output.resolved, "marker-evidence.json");
  const knowledgePath = path.join(output.resolved, "knowledge-candidate.json");
  await Promise.all([
    fs.writeFile(markerPath, `${JSON.stringify(closeout.markerEvidence, null, 2)}\n`, "utf8"),
    fs.writeFile(knowledgePath, `${JSON.stringify(closeout.knowledgeCandidate, null, 2)}\n`, "utf8"),
  ]);
  return {
    status: "written",
    output_directory: output.relative,
    marker: { id: closeout.markerEvidence.marker_id, percentage: closeout.markerEvidence.percentage },
    knowledge_candidate_id: closeout.knowledgeCandidate.candidate_id,
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
