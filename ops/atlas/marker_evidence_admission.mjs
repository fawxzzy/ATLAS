import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { runArtifactValidator } from "../../packages/atlas-contracts/scripts/validate-artifact.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const REGISTRY_REF = "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json";
const MARKER_SCHEMA_REF = "packages/atlas-contracts/schemas/atlas.marker-evidence.v2.schema.json";
const MARKER_SCHEMA_ID = "atlas.marker-evidence.v2";
const JOB_SCHEMA_ID = "atlas.job-envelope.v2";
const RECEIPT_SCHEMA_ID = "atlas.execution-receipt.v2";
const MARKER_ID = "lane-atlas-contracts-mesh";
const ADOPTED_FAMILY = "MarkerEvidence";
const ROLLUP_POLICY = "child-evidence-no-rollup";
const EXPECTED_NUMERATOR = 10;
const EXPECTED_DENOMINATOR = 11;
const EXPECTED_PERCENTAGE = Math.round((EXPECTED_NUMERATOR / EXPECTED_DENOMINATOR) * 100);
const EXPECTED_PRIOR_NUMERATOR = 9;
const EXPECTED_PRIOR_PERCENTAGE = Math.round((EXPECTED_PRIOR_NUMERATOR / EXPECTED_DENOMINATOR) * 100);

export const REQUIRED_MARKER_EVIDENCE_REFS = Object.freeze([
  REGISTRY_REF,
  MARKER_SCHEMA_REF,
  "ops/atlas/marker_evidence_admission.mjs",
  "tests/test_atlas_marker_evidence_admission.mjs",
  "ops/atlas/validate_contracts_v2_adoption.mjs",
  "ops/atlas/test_validate_contracts_v2_adoption.mjs",
  "docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-5-MARKEREVIDENCE-ADOPTION-2026-07-15.md",
]);

const MUTATION_FLAGS = Object.freeze([
  "--apply",
  "--write",
  "--ratchet",
  "--live",
  "--send",
  "--discord",
  "--deploy",
  "--production",
  "--prod",
]);

export class MarkerEvidenceAdmissionError extends Error {
  constructor(reasonCode, errors) {
    super(errors.join("; "));
    this.name = "MarkerEvidenceAdmissionError";
    this.reasonCode = reasonCode;
    this.errors = errors;
  }
}

function reject(reasonCode, error) {
  throw new MarkerEvidenceAdmissionError(reasonCode, [error]);
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

export function stableStringify(value) {
  return JSON.stringify(canonicalize(value));
}

function digest(bytes) {
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

function identity(prefix, value) {
  return `${prefix}_${digest(Buffer.from(stableStringify(value))).slice("sha256:".length, "sha256:".length + 32)}`;
}

function equalStringSet(actual, expected) {
  return Array.isArray(actual)
    && actual.length === expected.length
    && [...actual].sort().join("\n") === [...expected].sort().join("\n");
}

function isWithin(root, target) {
  return target === root || target.startsWith(`${root}${path.sep}`);
}

async function safeInput(input, workspaceRoot) {
  const resolved = path.resolve(input);
  if (!isWithin(workspaceRoot, resolved)) reject("MARKER_SCOPE_MISMATCH", "input path escaped the admitted workspace");
  let real;
  try {
    real = await fs.realpath(resolved);
  } catch {
    reject("MARKER_INPUT_MISSING", "required admission input is missing");
  }
  if (real !== resolved) reject("MARKER_SCOPE_MISMATCH", "input path did not resolve to its exact admitted identity");
  return resolved;
}

async function validateCanonical(schema, artifact, reasonCode) {
  const outcome = await runArtifactValidator(["--schema", schema, "--artifact", artifact, "--json"]);
  if (!outcome.result.ok) reject(reasonCode, `${schema} canonical validation failed: ${outcome.result.code}`);
  return outcome.result;
}

function findMarkerLane(registry) {
  if (registry?.schema !== "atlas.full_system_reevaluation.lanes.v1") {
    reject("MARKER_SCOPE_MISMATCH", "unexpected marker registry schema");
  }
  const candidates = [...(registry.lanes ?? []), ...(registry.backlog_candidates ?? [])];
  const matches = candidates.filter((candidate) => candidate?.id === MARKER_ID);
  if (matches.length !== 1) reject("MARKER_SCOPE_MISMATCH", "canonical marker registry identity was missing or duplicated");
  return matches[0];
}

function validateScope(marker, lane) {
  const source = marker.extensions?.source;
  if (
    marker.marker_id !== MARKER_ID
    || marker.marker_id !== lane.id
    || marker.scope !== lane.scope
    || source?.registry_ref !== REGISTRY_REF
    || source?.parent_lane_id !== lane.parent_lane_id
    || source?.measurement_unit !== lane.measurement_unit
    || source?.denominator_kind !== lane.denominator?.kind
    || source?.denominator_basis !== lane.denominator?.basis
  ) {
    reject("MARKER_SCOPE_MISMATCH", "marker scope or source identity disagreed with the canonical registry lane");
  }
}

function validatePercentage(marker, lane) {
  const expected = Math.round((marker.numerator / marker.denominator) * 100);
  if (
    !Number.isInteger(marker.numerator)
    || !Number.isInteger(marker.denominator)
    || marker.numerator !== lane.completed_units
    || marker.denominator !== lane.implementation_foundations
    || marker.denominator !== lane.denominator?.value
    || marker.numerator !== EXPECTED_NUMERATOR
    || marker.denominator !== EXPECTED_DENOMINATOR
    || marker.percentage !== EXPECTED_PERCENTAGE
    || marker.numerator > marker.denominator
    || marker.percentage !== expected
    || marker.percentage !== lane.percentage
  ) {
    reject("MARKER_PERCENTAGE_MISMATCH", "marker numerator, denominator, percentage, or rounded math disagreed with producer truth");
  }
}

function validateFreshness(marker, lane, executionReceipt) {
  const measuredAt = Date.parse(marker.measured_at);
  const recordedAt = Date.parse(executionReceipt.recorded_at);
  const validUntil = marker.freshness?.valid_until === null ? null : Date.parse(marker.freshness?.valid_until);
  if (
    marker.measured_at !== lane.last_audited_at
    || executionReceipt.recorded_at !== marker.measured_at
    || marker.freshness?.status !== "current"
    || !Number.isFinite(measuredAt)
    || !Number.isFinite(recordedAt)
    || measuredAt > recordedAt
    || (validUntil !== null && (!Number.isFinite(validUntil) || validUntil < recordedAt))
  ) {
    reject("MARKER_STALE", "marker freshness did not cover the correlated execution receipt and canonical audit time");
  }
}

function validateTransition(marker) {
  const adoption = marker.extensions?.adoption;
  if (
    adoption?.family !== ADOPTED_FAMILY
    || adoption?.prior_completed_units !== EXPECTED_PRIOR_NUMERATOR
    || adoption?.current_completed_units !== EXPECTED_NUMERATOR
    || marker.transition?.previous_percentage !== EXPECTED_PRIOR_PERCENTAGE
    || marker.transition?.current_percentage !== marker.percentage
  ) {
    reject("MARKER_TRANSITION_MISMATCH", "marker transition did not represent the single-family MarkerEvidence adoption ratchet");
  }
}

function validateRollup(marker, lane, job, executionReceipt) {
  if (
    marker.rollup_policy !== ROLLUP_POLICY
    || marker.extensions?.source?.parent_lane_id !== lane.parent_lane_id
    || marker.extensions?.authority?.parent_marker_movement !== false
    || job.extensions?.parent_marker_movement !== false
    || executionReceipt.extensions?.parent_marker_movement !== false
  ) {
    reject("MARKER_ROLLUP_MISMATCH", "MarkerEvidence adoption attempted to change or ambiguously roll up to its parent marker");
  }
}

async function validateEvidenceRefs(marker, executionReceipt) {
  if (
    !equalStringSet(marker.evidence_refs, REQUIRED_MARKER_EVIDENCE_REFS)
    || !equalStringSet(executionReceipt.evidence_refs, REQUIRED_MARKER_EVIDENCE_REFS)
  ) {
    reject("MARKER_EVIDENCE_REF_MISMATCH", "marker and execution receipt evidence references were incomplete or divergent");
  }
  for (const reference of REQUIRED_MARKER_EVIDENCE_REFS) {
    const expected = path.resolve(ROOT, ...reference.split("/"));
    let real;
    try {
      real = await fs.realpath(expected);
    } catch {
      reject("MARKER_EVIDENCE_REF_MISMATCH", `durable evidence reference is missing: ${reference}`);
    }
    if (real !== expected) reject("MARKER_EVIDENCE_REF_MISMATCH", `durable evidence reference changed identity: ${reference}`);
  }
}

function validateReceiptLineage(marker, job, executionReceipt, markerDigest) {
  const adoption = marker.extensions?.adoption;
  const binding = executionReceipt.extensions?.marker_evidence_binding;
  const jobCommands = job.verification?.commands ?? [];
  const passedCommands = new Set(
    (executionReceipt.verification ?? [])
      .filter((entry) => entry?.status === "passed")
      .map((entry) => entry.command),
  );
  const createdAt = Date.parse(job.created_at);
  const recordedAt = Date.parse(executionReceipt.recorded_at);
  if (
    adoption?.job_id !== job.job_id
    || adoption?.execution_receipt_id !== executionReceipt.receipt_id
    || job.job_id !== executionReceipt.job_id
    || job.component_id !== executionReceipt.component_id
    || job.project_id !== executionReceipt.project_id
    || job.correlations?.card_id !== marker.marker_id
    || executionReceipt.correlations?.card_id !== marker.marker_id
    || job.expected_receipt_version !== executionReceipt.contract_version
    || stableStringify(job.runtime) !== stableStringify(executionReceipt.runtime_effective)
    || !Number.isFinite(createdAt)
    || !Number.isFinite(recordedAt)
    || createdAt > recordedAt
    || job.authority?.external_mutations?.length !== 0
    || job.authority?.production_deploy !== false
    || job.authority?.destructive_actions !== false
    || executionReceipt.status !== "succeeded"
    || executionReceipt.blockers?.length !== 0
    || executionReceipt.changed_paths?.length !== 0
    || executionReceipt.commits?.length !== 0
    || executionReceipt.authority_actions?.length !== 0
    || stableStringify(executionReceipt.follow_up) !== stableStringify(["KnowledgeCandidate"])
    || executionReceipt.extensions?.external_mutation !== false
    || executionReceipt.extensions?.marker_mutation !== false
    || marker.extensions?.authority?.external_mutation !== false
    || marker.extensions?.authority?.marker_mutation !== false
    || binding?.marker_id !== marker.marker_id
    || binding?.digest !== markerDigest
    || jobCommands.length === 0
    || jobCommands.some((command) => !passedCommands.has(command))
  ) {
    reject("MARKER_RECEIPT_MISMATCH", "job, execution receipt, marker digest, verification, or read-only authority lineage did not correlate");
  }
}

export async function buildMarkerAdmissionReceipt({
  markerPath,
  jobPath,
  executionReceiptPath,
  registryPath = path.join(ROOT, REGISTRY_REF),
  workspaceRoot = ROOT,
}) {
  const admittedRoot = path.resolve(workspaceRoot);
  const [safeMarker, safeJob, safeExecutionReceipt, safeRegistry] = await Promise.all([
    safeInput(markerPath, admittedRoot),
    safeInput(jobPath, admittedRoot),
    safeInput(executionReceiptPath, admittedRoot),
    safeInput(registryPath, admittedRoot),
  ]);
  if (safeRegistry !== path.join(admittedRoot, ...REGISTRY_REF.split("/"))) {
    reject("MARKER_SCOPE_MISMATCH", "consumer was pointed at a non-canonical marker registry");
  }

  const [markerValidation, jobValidation, receiptValidation] = await Promise.all([
    validateCanonical(MARKER_SCHEMA_ID, safeMarker, "MARKER_SCHEMA_INVALID"),
    validateCanonical(JOB_SCHEMA_ID, safeJob, "MARKER_RECEIPT_MISMATCH"),
    validateCanonical(RECEIPT_SCHEMA_ID, safeExecutionReceipt, "MARKER_RECEIPT_MISMATCH"),
  ]);
  const [markerBytes, jobBytes, executionReceiptBytes, registryBytes, schemaBytes, packageBytes] = await Promise.all([
    fs.readFile(safeMarker),
    fs.readFile(safeJob),
    fs.readFile(safeExecutionReceipt),
    fs.readFile(safeRegistry),
    fs.readFile(path.join(ROOT, MARKER_SCHEMA_REF)),
    fs.readFile(path.join(ROOT, "packages/atlas-contracts/package.json")),
  ]);
  const marker = JSON.parse(markerBytes);
  const job = JSON.parse(jobBytes);
  const executionReceipt = JSON.parse(executionReceiptBytes);
  const registry = JSON.parse(registryBytes);
  const packageMetadata = JSON.parse(packageBytes);
  const lane = findMarkerLane(registry);
  const markerDigest = digest(markerBytes);

  validateScope(marker, lane);
  validatePercentage(marker, lane);
  validateFreshness(marker, lane, executionReceipt);
  validateTransition(marker);
  validateRollup(marker, lane, job, executionReceipt);
  await validateEvidenceRefs(marker, executionReceipt);
  validateReceiptLineage(marker, job, executionReceipt, markerDigest);

  const inputIdentity = {
    marker_evidence: markerDigest,
    job_envelope: digest(jobBytes),
    execution_receipt: digest(executionReceiptBytes),
    source_registry: digest(registryBytes),
  };
  const resultBasis = {
    marker_id: marker.marker_id,
    adopted_family: ADOPTED_FAMILY,
    numerator: marker.numerator,
    denominator: marker.denominator,
    percentage: marker.percentage,
    previous_percentage: marker.transition.previous_percentage,
    measured_at: marker.measured_at,
    job_id: job.job_id,
    execution_receipt_id: executionReceipt.receipt_id,
  };
  const resultIdentity = { result_id: identity("ameres", resultBasis), ...resultBasis };
  const receiptBasis = {
    contract_version: "atlas.marker-evidence-admission-receipt.v1",
    status: "accepted_read_only",
    reason_code: "ACCEPTED",
    recorded_at: executionReceipt.recorded_at,
    input_identity: inputIdentity,
    result_identity: resultIdentity,
    schema_source: {
      package_name: packageMetadata.name,
      package_version: packageMetadata.version,
      validator_reference: "packages/atlas-contracts/scripts/validate-artifact.mjs",
      semantic_validator_reference: "packages/atlas-contracts/scripts/lib/validate-semantics.mjs",
      schema_id: markerValidation.schema.id,
      schema_file: markerValidation.schema.file,
      schema_digest: digest(schemaBytes),
      job_schema_id: jobValidation.schema.id,
      execution_receipt_schema_id: receiptValidation.schema.id,
    },
    conformance: {
      scope_identity: true,
      percentage_math: true,
      freshness: true,
      transition: true,
      rollup_identity: true,
      execution_receipt_lineage: true,
      evidence_identity: true,
    },
    authority: {
      read_only: true,
      external_mutation: false,
      marker_mutation: false,
      parent_marker_movement: false,
    },
  };
  return { receipt_id: identity("amer", receiptBasis), ...receiptBasis };
}

export function verifyMarkerConsumerReceipt(receipt, expectedReceipt) {
  if (!receipt) reject("MARKER_CONSUMER_RECEIPT_MISSING", "independent MarkerEvidence consumer receipt is missing");
  if (!expectedReceipt || stableStringify(receipt) !== stableStringify(expectedReceipt)) {
    reject("MARKER_CONSUMER_RECEIPT_MISMATCH", "independent MarkerEvidence consumer receipt changed identity or result");
  }
  return true;
}

export function parseArgs(argv) {
  if (argv.some((argument) => MUTATION_FLAGS.includes(argument.split("=", 1)[0]))) {
    reject("MARKER_MUTATION_NOT_ADMITTED", "MarkerEvidence admission is read-only and accepts no mutation flag");
  }
  const options = { json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--json") {
      options.json = true;
      continue;
    }
    const match = argument.match(/^--(marker|job|receipt|registry)=(.+)$/);
    if (match) {
      options[match[1]] = match[2];
      continue;
    }
    if (["--marker", "--job", "--receipt", "--registry"].includes(argument)) {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) reject("MARKER_INPUT_MISSING", `${argument} requires a path`);
      options[argument.slice(2)] = value;
      index += 1;
      continue;
    }
    reject("MARKER_INPUT_MISSING", `unsupported argument: ${argument}`);
  }
  if (!options.marker || !options.job || !options.receipt) {
    reject("MARKER_INPUT_MISSING", "--marker, --job, and --receipt are required");
  }
  return options;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const receipt = await buildMarkerAdmissionReceipt({
      markerPath: args.marker,
      jobPath: args.job,
      executionReceiptPath: args.receipt,
      registryPath: args.registry,
    });
    console.log(args.json ? JSON.stringify(receipt) : `ACCEPTED: ${receipt.receipt_id}`);
  } catch (error) {
    const result = {
      ok: false,
      reasonCode: error?.reasonCode ?? "MARKER_ADMISSION_FAILED",
      errors: error?.errors ?? [error?.message ?? "MarkerEvidence admission failed"],
    };
    console.log(JSON.stringify(result));
    process.exitCode = 1;
  }
}
