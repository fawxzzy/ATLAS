import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { runArtifactValidator } from "../../packages/atlas-contracts/scripts/validate-artifact.mjs";
import {
  buildMarkerAdmissionReceipt,
  stableStringify as stableAdmissionStringify,
  verifyMarkerConsumerReceipt,
} from "./marker_evidence_admission.mjs";
import { buildBoardEvent } from "./native_board_correlation.mjs";

export const EXPECTED_FAMILIES = Object.freeze([
  "componentManifest",
  "jobEnvelope",
  "contextPacket",
  "approvalRecord",
  "workerLease",
  "evidenceBundle",
  "executionReceipt",
]);
export const CARD_BOARD_FAMILIES = Object.freeze(["cardRecord", "boardEvent"]);
export const MARKER_EVIDENCE_FAMILIES = Object.freeze(["markerEvidence"]);
export const ADOPTED_FAMILIES = Object.freeze([...EXPECTED_FAMILIES, ...CARD_BOARD_FAMILIES, ...MARKER_EVIDENCE_FAMILIES]);

const SCHEMAS = Object.freeze({
  componentManifest: "atlas.component-manifest.v2",
  jobEnvelope: "atlas.job-envelope.v2",
  contextPacket: "atlas.context-packet.v2",
  approvalRecord: "atlas.approval-record.v2",
  workerLease: "atlas.worker-lease.v2",
  evidenceBundle: "atlas.evidence-bundle.v2",
  executionReceipt: "atlas.execution-receipt.v2",
  cardRecord: "atlas.card-record.v2",
  boardEvent: "atlas.board-event.v2",
  markerEvidence: "atlas.marker-evidence.v2",
});
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const VALIDATOR = path.join(ROOT, "packages", "atlas-contracts", "scripts", "validate-artifact.mjs");
const EXTERNAL_ACTIONS = Object.freeze(["push", "deploy", "production", "discord", "board", "data_mutation"]);
const DISCORDOS_ROOT = path.join(ROOT, "repos", "DiscordOS");
const DISCORDOS_CONSUMER_MERGE = "b2dbcc1a9ca66876e9c07ea8c6032701c9aaea2a";
const DISCORDOS_CONSUMER_PATHS = Object.freeze([
  "scripts/discordos-atlas-card-board-consumer.mjs",
  "tests/discordos-atlas-card-board-consumer.test.mjs",
  "docs/ops/discordos-atlas-contracts-v2-card-board-consumer-2026-07-15.md",
  "package.json",
]);
const CARD_FIXTURE = path.join(ROOT, "packages", "atlas-contracts", "fixtures", "valid", "card-record.v2.json");
const CARD_EXPORT = path.join(ROOT, "docs", "registry", "project-board-owner-exports", "atlas.project-board.owner-export.v1.json");
const LANE_REGISTRY = path.join(ROOT, "docs", "registry", "ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json");
const MESH_LANE_ID = "lane-atlas-contracts-mesh";
const PRODUCER_CARD_ID = "MAZER-142";
const PRODUCER_PROJECT_ID = "mazer";
const PRODUCER_BOARD_ID = "discordos:project-feedback:mazer";
const MESH_COMPLETED_UNITS = 10;
const MESH_FOUNDATIONS = 11;
const MESH_PERCENTAGE = Math.round((MESH_COMPLETED_UNITS / MESH_FOUNDATIONS) * 100);
const MESH_PRIOR_COMPLETED_UNITS = 9;
const MESH_PRIOR_PERCENTAGE = Math.round((MESH_PRIOR_COMPLETED_UNITS / MESH_FOUNDATIONS) * 100);
const CARD_BOARD_JOB_ID = "job-atlas-contracts-v2-card-board-adoption";
const CARD_BOARD_OCCURRED_AT = "2026-07-15T15:05:00Z";
const MARKER_JOB_ID = "job-atlas-contracts-v2-marker-evidence-adoption";
const MARKER_EXECUTION_RECEIPT_ID = "atr_marker_evidence_adoption_20260715";
const MARKER_CONSUMER_REF = "ops/atlas/marker_evidence_admission.mjs";
const MARKER_RECEIPT_REF = "docs/ops/ATLAS-CONTRACTS-V2-CLUSTER-5-MARKEREVIDENCE-ADOPTION-2026-07-15.md";
const MARKER_EVIDENCE_REFS = Object.freeze([
  "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
  "packages/atlas-contracts/schemas/atlas.marker-evidence.v2.schema.json",
  MARKER_CONSUMER_REF,
  "tests/test_atlas_marker_evidence_admission.mjs",
  "ops/atlas/validate_contracts_v2_adoption.mjs",
  "ops/atlas/test_validate_contracts_v2_adoption.mjs",
  MARKER_RECEIPT_REF,
]);
const MUTATION_FLAGS = Object.freeze(["--apply", "--live", "--write", "--send", "--storage", "--discord", "--deploy", "--production", "--prod"]);
let discordOsConsumerModule;

function relative(file) { return path.relative(ROOT, file).split(path.sep).join("/"); }
function fail(reasonCode, errors) { return { ok: false, code: reasonCode, reasonCode, errors }; }
async function readJson(file) { return JSON.parse(await fs.readFile(file, "utf8")); }
function isRecord(value) { return Boolean(value) && typeof value === "object" && !Array.isArray(value); }
function resolvedPath(value) { return typeof value === "string" ? path.resolve(value) : null; }
function sha256(bytes) { return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`; }
function stableBytes(value) { return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, "utf8"); }

async function loadDiscordOsConsumer() {
  if (!discordOsConsumerModule) {
    discordOsConsumerModule = await import(pathToFileURL(path.join(DISCORDOS_ROOT, "scripts", "discordos-atlas-card-board-consumer.mjs")).href);
  }
  return discordOsConsumerModule;
}

function runGit(args) {
  return spawnSync("git", ["-C", DISCORDOS_ROOT, ...args], { encoding: "utf8", windowsHide: true });
}

function consumerGitEvidence() {
  const head = runGit(["rev-parse", "HEAD"]);
  const ancestor = runGit(["merge-base", "--is-ancestor", DISCORDOS_CONSUMER_MERGE, "HEAD"]);
  const unchanged = runGit(["diff", "--quiet", `${DISCORDOS_CONSUMER_MERGE}..HEAD`, "--", ...DISCORDOS_CONSUMER_PATHS]);
  const status = runGit(["status", "--short", "--untracked-files=no"]);
  if (head.status !== 0 || ancestor.status !== 0 || unchanged.status !== 0 || status.status !== 0 || status.stdout.trim()) return null;
  return { mergeCommit: DISCORDOS_CONSUMER_MERGE, head: head.stdout.trim(), trackedClean: true, consumerFilesUnchanged: true };
}

function mapConsumerRejection(error) {
  if (error?.reasonCode === "card_schema_invalid") return "CARD_RECORD_SCHEMA_INVALID";
  if (error?.reasonCode === "event_schema_invalid") return "BOARD_EVENT_SCHEMA_INVALID";
  const errors = new Set(error?.errors ?? []);
  const mapping = [
    ["card_id_mismatch", "BOARD_EVENT_CARD_MISMATCH"],
    ["board_id_mismatch", "BOARD_EVENT_BOARD_MISMATCH"],
    ["expected_version_mismatch", "BOARD_EVENT_VERSION_MISMATCH"],
    ["from_state_mismatch", "BOARD_EVENT_FROM_STATE_MISMATCH"],
    ["writer_authority_mismatch", "WRITER_AUTHORITY_MISMATCH"],
    ["event_idempotency_key_unstable", "BOARD_EVENT_IDEMPOTENCY_MISMATCH"],
    ["event_id_unstable", "BOARD_EVENT_IDENTITY_MISMATCH"],
    ["authority_drift_detected", "SECOND_WRITER_AUTHORITY"],
    ["pending_result_claims_readback_or_error", "BOARD_EVENT_RESULT_MISMATCH"],
    ["observed_result_missing_readback_fields", "BOARD_EVENT_RESULT_MISMATCH"],
    ["failed_result_missing_error_code", "BOARD_EVENT_RESULT_MISMATCH"],
  ];
  return mapping.find(([source]) => errors.has(source))?.[1] ?? "DISCORDOS_CONSUMER_REJECTED";
}

async function loadCanonicalMeshCard() {
  const [card, ownerExport, registry] = await Promise.all([readJson(CARD_FIXTURE), readJson(CARD_EXPORT), readJson(LANE_REGISTRY)]);
  const cardEnvelope = ownerExport.cards?.find((candidate) => candidate?.record?.card_id === MESH_LANE_ID);
  const lane = [...(registry.lanes ?? []), ...(registry.backlog_candidates ?? [])].find((candidate) => candidate?.id === MESH_LANE_ID);
  if (!cardEnvelope || !lane) throw new Error("canonical mesh projection missing");
  const projectionCard = cardEnvelope.record;
  const projectionMatches = lane.percentage === MESH_PERCENTAGE
    && lane.completed_units === MESH_COMPLETED_UNITS
    && lane.implementation_foundations === MESH_FOUNDATIONS
    && lane.denominator?.value === MESH_FOUNDATIONS
    && projectionCard.extensions?.percentage === lane.percentage
    && projectionCard.extensions?.completed_units === lane.completed_units
    && projectionCard.extensions?.denominator?.value === lane.denominator?.value
    && projectionCard.updated_at === lane.last_audited_at
    && cardEnvelope.source?.source_updated_at === lane.last_audited_at;
  if (!projectionMatches) throw new Error("mesh marker and CardRecord projection mismatch");
  return { card, lane, ownerExport };
}

function buildCardBoardJob(card) {
  return {
    contract_version: "atlas.job-envelope.v2",
    job_id: CARD_BOARD_JOB_ID,
    project_id: card.project_id,
    created_at: "2026-07-15T15:04:00Z",
    component_id: "atlas-root",
    objective: "Independently prove CardRecord and BoardEvent adoption without external mutation.",
    scope: { owner_repository: "atlas", allowed_paths: ["docs/**", "ops/atlas/**", "packages/atlas-contracts/**"], forbidden_paths: ["secrets/**", "repos/**"] },
    runtime: { model: "gpt-5.6-sol", reasoning: "xhigh", speed: "standard", permissions: "full-access", approval_policy: "never" },
    authority: { external_mutations: [], production_deploy: false, destructive_actions: false },
    verification: { commands: ["node ops/atlas/test_validate_contracts_v2_adoption.mjs"], evidence_required: ["deterministic no-storage DiscordOS consumer receipt"] },
    correlations: { card_id: card.card_id, parent_job_id: null },
    expected_receipt_version: "atlas.execution-receipt.v2",
    extensions: { adoption_cluster: 4 },
  };
}

function buildCardBoardReceipt(card) {
  return {
    contract_version: "atlas.execution-receipt.v2",
    receipt_id: "atr_card_board_adoption_20260715",
    job_id: CARD_BOARD_JOB_ID,
    recorded_at: CARD_BOARD_OCCURRED_AT,
    status: "succeeded",
    component_id: "atlas-root",
    project_id: card.project_id,
    runtime_effective: { model: "gpt-5.6-sol", reasoning: "xhigh", speed: "standard", permissions: "full-access", approval_policy: "never" },
    changed_paths: [],
    commits: [],
    verification: [],
    evidence_refs: [],
    blockers: [],
    follow_up: ["MarkerEvidence", "KnowledgeCandidate"],
    correlations: { card_id: card.card_id, thread_id: "019f52d9-7667-72a3-a5f7-9c0613aedd8f", turn_id: "contracts-v2-cluster-4", branch: "codex/atlas-contracts-v2-card-board-adoption", worktree: null },
    authority_actions: [],
    summary: "CardRecord and BoardEvent independent consumer adoption proof.",
    extensions: { external_mutation: false },
  };
}

export async function buildCanonicalCardBoardEvidence() {
  const { card, lane, ownerExport } = await loadCanonicalMeshCard();
  const job = buildCardBoardJob(card);
  const receipt = buildCardBoardReceipt(card);
  const event = await buildBoardEvent({
    job,
    receipt,
    card,
    eventType: "transition",
    occurredAt: CARD_BOARD_OCCURRED_AT,
    fromState: card.lifecycle,
    toState: "review",
    reason: "Independent CardRecord and BoardEvent adoption proof accepted.",
  });
  return { card, event, job, receipt, lane, ownerExport };
}

function mutationArgumentsFailClosed(consumer) {
  return MUTATION_FLAGS.every((flag) => {
    try {
      consumer.parseArgs(["--card", "card.json", "--event", "event.json", flag]);
      return false;
    } catch (error) {
      return error?.reasonCode === "mutation_not_admitted";
    }
  });
}

export async function validateCardBoardArtifacts(card, event) {
  const temp = await fs.mkdtemp(path.join(ROOT, "tmp", "atlas-contracts-v2-card-board-adoption-"));
  const cardPath = path.join(temp, "card-record.json");
  const eventPath = path.join(temp, "board-event.json");
  const cardBytes = stableBytes(card);
  const eventBytes = stableBytes(event);
  try {
    await Promise.all([fs.writeFile(cardPath, cardBytes), fs.writeFile(eventPath, eventBytes)]);
    const [cardValidation, eventValidation] = await Promise.all([
      validateArtifact("cardRecord", cardPath),
      validateArtifact("boardEvent", eventPath),
    ]);
    if (!cardValidation.result.ok) return fail("CARD_RECORD_SCHEMA_INVALID", ["CardRecord canonical schema validation failed"]);
    if (!eventValidation.result.ok) return fail("BOARD_EVENT_SCHEMA_INVALID", ["BoardEvent canonical schema validation failed"]);
    if (card.card_id !== PRODUCER_CARD_ID || card.project_id !== PRODUCER_PROJECT_ID || card.board_id !== PRODUCER_BOARD_ID) {
      return fail("CARD_RECORD_PROJECT_MISMATCH", ["CardRecord card, project, or board source identity mismatch"]);
    }

    let first;
    let second;
    let consumer;
    const originalCwd = process.cwd();
    try {
      process.chdir(DISCORDOS_ROOT);
      consumer = await loadDiscordOsConsumer();
      first = await consumer.buildConsumerReceipt({ cardPath, eventPath, cwd: DISCORDOS_ROOT });
      second = await consumer.buildConsumerReceipt({ cardPath, eventPath, cwd: DISCORDOS_ROOT });
    } catch (error) {
      return fail(mapConsumerRejection(error), error?.errors?.length ? error.errors : [error?.reasonCode ?? "consumer failure"]);
    } finally {
      process.chdir(originalCwd);
    }

    const [cardSchemaBytes, eventSchemaBytes, packageMetadata] = await Promise.all([
      fs.readFile(path.join(ROOT, "packages", "atlas-contracts", "schemas", "atlas.card-record.v2.schema.json")),
      fs.readFile(path.join(ROOT, "packages", "atlas-contracts", "schemas", "atlas.board-event.v2.schema.json")),
      readJson(path.join(ROOT, "packages", "atlas-contracts", "package.json")),
    ]);
    const schemaSourceMatches = first.schema_source?.package_name === "@atlas/contracts"
      && first.schema_source?.package_version === packageMetadata.version
      && first.schema_source?.resolution === "atlas_layout_default"
      && first.schema_source?.validator_reference === "packages/atlas-contracts/scripts/lib/validate-json-schema.mjs"
      && first.schema_source?.semantic_validator_reference === "packages/atlas-contracts/scripts/lib/validate-semantics.mjs"
      && first.canonical_schema_validation?.card_record?.schema_id === SCHEMAS.cardRecord
      && first.canonical_schema_validation?.card_record?.schema_digest === sha256(cardSchemaBytes)
      && first.canonical_schema_validation?.board_event?.schema_id === SCHEMAS.boardEvent
      && first.canonical_schema_validation?.board_event?.schema_digest === sha256(eventSchemaBytes);
    if (!schemaSourceMatches) return fail("CANONICAL_SCHEMA_SOURCE_MISMATCH", ["DiscordOS did not bind the Atlas-owned validator and schemas"]);
    if (consumer.stableStringify(first) !== consumer.stableStringify(second)) return fail("CONSUMER_RECEIPT_NONDETERMINISTIC", ["identical replay changed the consumer receipt"]);

    const receiptMatches = first.ok === true
      && first.status === "admitted_dry_run"
      && first.card_record?.contract_version === SCHEMAS.cardRecord
      && first.card_record?.card_id === card.card_id
      && first.card_record?.project_id === card.project_id
      && first.card_record?.board_id === card.board_id
      && first.card_record?.board_version === card.board_version
      && first.card_record?.lifecycle === card.lifecycle
      && first.board_event?.contract_version === SCHEMAS.boardEvent
      && first.board_event?.event_id === event.event_id
      && first.board_event?.idempotency_key === event.idempotency_key
      && first.input_digests?.card_record === sha256(cardBytes)
      && first.input_digests?.board_event === sha256(eventBytes)
      && first.semantic_consumption?.card_id_matches === true
      && first.semantic_consumption?.board_id_matches === true
      && first.semantic_consumption?.expected_version_matches === true
      && first.semantic_consumption?.from_state_matches === true
      && first.semantic_consumption?.event_identity_stable === true
      && first.semantic_consumption?.result_semantics_valid === true
      && first.semantic_consumption?.lifecycle_sync?.status === "sync_ready"
      && first.writer_boundary?.writer_authority === "discordos"
      && first.writer_boundary?.sole_logical_writer === true
      && first.writer_boundary?.external_mutation === false
      && first.writer_boundary?.storage_applied === false
      && first.writer_boundary?.storage_writes_allowed === false
      && first.writer_boundary?.live_behavior_allowed === false
      && first.writer_boundary?.messages_sent === false
      && first.writer_boundary?.authority_drift === false;
    if (!receiptMatches) return fail("CONSUMER_RECEIPT_MISMATCH", ["DiscordOS deterministic dry-run receipt lost identity, source, or authority bindings"]);
    if (!mutationArgumentsFailClosed(consumer)) return fail("MUTATION_FLAG_ADMITTED", ["DiscordOS consumer admitted a write, send, deploy, or production flag"]);

    return {
      ok: true,
      code: "ACCEPTED",
      reasonCode: "ACCEPTED",
      families: CARD_BOARD_FAMILIES,
      receipt: first,
      evidence: {
        cardRecord: { path: relative(CARD_FIXTURE), bytes: cardBytes.length, sha256: sha256(cardBytes) },
        boardEvent: { producer: "ops/atlas/native_board_correlation.mjs", bytes: eventBytes.length, sha256: sha256(eventBytes) },
      },
    };
  } finally {
    await fs.rm(temp, { recursive: true, force: true });
  }
}

export async function validateCardBoardAdoption() {
  const gitEvidence = consumerGitEvidence();
  if (!gitEvidence) return fail("DISCORDOS_CONSUMER_GIT_MISMATCH", ["DiscordOS consumer merge, source stability, or tracked-clean proof failed"]);
  let producer;
  try { producer = await buildCanonicalCardBoardEvidence(); } catch (error) {
    return fail("CARD_RECORD_PROJECTION_MISMATCH", [error.message]);
  }
  const result = await validateCardBoardArtifacts(producer.card, producer.event);
  return result.ok ? { ...result, consumerGit: gitEvidence } : result;
}

export async function buildCanonicalMarkerEvidence() {
  const { lane } = await loadCanonicalMeshCard();
  const runtime = { model: "gpt-5.6-sol", reasoning: "xhigh", speed: "standard", permissions: "full-access", approval_policy: "never" };
  const marker = {
    contract_version: SCHEMAS.markerEvidence,
    marker_id: lane.id,
    scope: lane.scope,
    measured_at: lane.last_audited_at,
    numerator: lane.completed_units,
    denominator: lane.denominator.value,
    percentage: lane.percentage,
    evidence_refs: [...MARKER_EVIDENCE_REFS],
    freshness: { status: "current", valid_until: null },
    transition: {
      previous_percentage: MESH_PRIOR_PERCENTAGE,
      current_percentage: lane.percentage,
      reason: "MarkerEvidence gained independent read-only admission, deterministic receipt, and negative conformance proof.",
    },
    rollup_policy: "child-evidence-no-rollup",
    extensions: {
      source: {
        registry_ref: relative(LANE_REGISTRY),
        parent_lane_id: lane.parent_lane_id,
        measurement_unit: lane.measurement_unit,
        denominator_kind: lane.denominator.kind,
        denominator_basis: lane.denominator.basis,
      },
      adoption: {
        family: "MarkerEvidence",
        prior_completed_units: MESH_PRIOR_COMPLETED_UNITS,
        current_completed_units: lane.completed_units,
        job_id: MARKER_JOB_ID,
        execution_receipt_id: MARKER_EXECUTION_RECEIPT_ID,
      },
      authority: {
        external_mutation: false,
        marker_mutation: false,
        parent_marker_movement: false,
        ratchet_requires_accepted_receipt: true,
      },
    },
  };
  const markerBytes = stableBytes(marker);
  const commands = [
    "node --test tests/test_atlas_marker_evidence_admission.mjs",
    "node ops/atlas/test_validate_contracts_v2_adoption.mjs",
  ];
  const job = {
    contract_version: SCHEMAS.jobEnvelope,
    job_id: MARKER_JOB_ID,
    component_id: "atlas-root",
    project_id: "atlas",
    created_at: new Date(Date.parse(lane.last_audited_at) - 60_000).toISOString(),
    objective: "Independently admit canonical MarkerEvidence without marker or external mutation.",
    scope: {
      owner_repository: "atlas",
      allowed_paths: ["docs/**", "ops/atlas/**", "packages/atlas-contracts/**", "tests/**"],
      forbidden_paths: ["secrets/**", "repos/**", "runtime/**"],
    },
    runtime,
    authority: { external_mutations: [], production_deploy: false, destructive_actions: false },
    verification: { commands, evidence_required: ["deterministic MarkerEvidence consumer receipt", "stable negative reason-code matrix"] },
    correlations: { card_id: lane.id, parent_job_id: null },
    expected_receipt_version: SCHEMAS.executionReceipt,
    extensions: {
      marker_id: lane.id,
      producer_registry_ref: relative(LANE_REGISTRY),
      prior_completed_units: MESH_PRIOR_COMPLETED_UNITS,
      target_completed_units: MESH_COMPLETED_UNITS,
      parent_marker_movement: false,
    },
  };
  const executionReceipt = {
    contract_version: SCHEMAS.executionReceipt,
    receipt_id: MARKER_EXECUTION_RECEIPT_ID,
    job_id: MARKER_JOB_ID,
    recorded_at: lane.last_audited_at,
    status: "succeeded",
    component_id: "atlas-root",
    project_id: "atlas",
    runtime_effective: runtime,
    changed_paths: [],
    commits: [],
    verification: commands.map((command) => ({ command, status: "passed", evidence_refs: [MARKER_RECEIPT_REF] })),
    evidence_refs: [...MARKER_EVIDENCE_REFS],
    blockers: [],
    follow_up: ["KnowledgeCandidate"],
    correlations: {
      card_id: lane.id,
      thread_id: "019f52d9-7667-72a3-a5f7-9c0613aedd8f",
      turn_id: "contracts-v2-cluster-5-marker-evidence",
      branch: "codex/atlas-contracts-v2-marker-evidence-adoption",
      worktree: null,
    },
    authority_actions: [],
    summary: "Read-only MarkerEvidence admission and adoption proof.",
    extensions: {
      marker_evidence_binding: {
        marker_id: lane.id,
        artifact_ref: "generated:ops/atlas/validate_contracts_v2_adoption.mjs#buildCanonicalMarkerEvidence",
        digest: sha256(markerBytes),
      },
      external_mutation: false,
      marker_mutation: false,
      parent_marker_movement: false,
    },
  };
  return { marker, job, executionReceipt, lane };
}

export async function validateMarkerEvidenceArtifacts(marker, job, executionReceipt, { consumerReceipt } = {}) {
  const temp = await fs.mkdtemp(path.join(ROOT, "tmp", "atlas-contracts-v2-marker-evidence-adoption-"));
  const markerPath = path.join(temp, "marker-evidence.json");
  const jobPath = path.join(temp, "job-envelope.json");
  const executionReceiptPath = path.join(temp, "execution-receipt.json");
  const markerBytes = stableBytes(marker);
  try {
    await Promise.all([
      fs.writeFile(markerPath, markerBytes),
      fs.writeFile(jobPath, stableBytes(job)),
      fs.writeFile(executionReceiptPath, stableBytes(executionReceipt)),
    ]);
    let first;
    let second;
    try {
      first = await buildMarkerAdmissionReceipt({ markerPath, jobPath, executionReceiptPath });
      second = await buildMarkerAdmissionReceipt({ markerPath, jobPath, executionReceiptPath });
    } catch (error) {
      return fail(error?.reasonCode ?? "MARKER_ADMISSION_FAILED", error?.errors ?? [error?.message ?? "MarkerEvidence admission failed"]);
    }
    if (stableAdmissionStringify(first) !== stableAdmissionStringify(second)) {
      return fail("MARKER_CONSUMER_RECEIPT_NONDETERMINISTIC", ["identical MarkerEvidence replay changed the consumer receipt"]);
    }
    const admittedReceipt = consumerReceipt === undefined ? first : consumerReceipt;
    try {
      verifyMarkerConsumerReceipt(admittedReceipt, first);
    } catch (error) {
      return fail(error?.reasonCode ?? "MARKER_CONSUMER_RECEIPT_MISMATCH", error?.errors ?? [error?.message ?? "MarkerEvidence consumer receipt verification failed"]);
    }
    return {
      ok: true,
      code: "ACCEPTED",
      reasonCode: "ACCEPTED",
      families: MARKER_EVIDENCE_FAMILIES,
      receipt: admittedReceipt,
      evidence: {
        markerEvidence: {
          producer: "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json",
          consumer: MARKER_CONSUMER_REF,
          bytes: markerBytes.length,
          sha256: sha256(markerBytes),
        },
      },
    };
  } finally {
    await fs.rm(temp, { recursive: true, force: true });
  }
}

export async function validateMarkerEvidenceAdoption() {
  let producer;
  try {
    producer = await buildCanonicalMarkerEvidence();
  } catch (error) {
    return fail("MARKER_PROJECTION_MISMATCH", [error.message]);
  }
  return validateMarkerEvidenceArtifacts(producer.marker, producer.job, producer.executionReceipt);
}

export async function validateAdoptedMesh(runPath) {
  const seven = await validateAdoption(runPath);
  if (!seven.ok) return seven;
  const cardBoard = await validateCardBoardAdoption();
  if (!cardBoard.ok) return cardBoard;
  const markerEvidence = await validateMarkerEvidenceAdoption();
  if (!markerEvidence.ok) return markerEvidence;
  return {
    ok: true,
    code: "ACCEPTED",
    reasonCode: "ACCEPTED",
    families: ADOPTED_FAMILIES,
    acceptedUnits: MESH_COMPLETED_UNITS,
    implementationFoundations: MESH_FOUNDATIONS,
    percentage: MESH_PERCENTAGE,
    runId: seven.runId,
    jobId: seven.jobId,
    consumerReceiptId: cardBoard.receipt.receipt_id,
    markerConsumerReceiptId: markerEvidence.receipt.receipt_id,
    consumerGit: cardBoard.consumerGit,
    evidence: { ...seven.evidence, ...cardBoard.evidence, ...markerEvidence.evidence },
  };
}

async function validateArtifact(family, file) {
  return runArtifactValidator(["--schema", SCHEMAS[family], "--artifact", file, "--json"]);
}

function producerValidationMatches(evidence, expected, file) {
  if (!isRecord(evidence) || evidence.invoked !== true || resolvedPath(evidence.cliPath) !== VALIDATOR) return false;
  if (evidence.schemaId !== SCHEMAS[expected.family] || resolvedPath(evidence.artifactPath) !== file) return false;
  if (evidence.exitCode !== expected.exitCode || evidence.ok !== expected.result.ok || evidence.reasonCode !== null) return false;
  if (JSON.stringify(evidence.result) !== JSON.stringify(expected.result)) return false;
  try { return JSON.stringify(JSON.parse(evidence.stdout)) === JSON.stringify(expected.result) && evidence.stderr === "" && evidence.parseError === null; } catch { return false; }
}

function artifactReferencesMatch(receipt, resolved) {
  const refs = receipt.extensions?.artifact_refs;
  if (!isRecord(refs) || !Array.isArray(receipt.evidence_refs)) return false;
  const expected = {
    context_packet: resolved.contextPacket,
    approval_record: resolved.approvalRecord,
    worker_lease: resolved.workerLease,
    evidence_bundle: resolved.evidenceBundle,
  };
  return Object.entries(expected).every(([key, file]) => resolvedPath(refs[key]) === file && receipt.evidence_refs.some((reference) => resolvedPath(reference) === file));
}

function hasTerminalVerificationEvidence(receipt, evidenceBundle) {
  const verificationRefs = new Set((receipt.verification ?? []).flatMap((entry) => entry?.status === "passed" ? entry.evidence_refs ?? [] : []).map(resolvedPath));
  return evidenceBundle.classifications?.includes("verified")
    && evidenceBundle.evidence?.some((entry) => entry?.status === "passed" && verificationRefs.has(resolvedPath(entry.ref)));
}

function authorityDenied(run, job, approval, receipt) {
  const denied = job.extensions?.external_authority;
  const notExercised = receipt.extensions?.external_authority;
  return job.authority?.external_mutations?.length === 0
    && job.authority?.production_deploy === false
    && job.authority?.destructive_actions === false
    && EXTERNAL_ACTIONS.every((action) => denied?.[action] === "denied" && notExercised?.[action] === "not-exercised")
    && approval.action?.kind === "external-mutation"
    && approval.decision === "rejected"
    && approval.extensions?.external_authority === "denied"
    && !run.authorityActions?.length
    && !run.mutationScopeViolations?.length
    && !run.effectivePolicies?.externalAuthorityAction
    && !receipt.authority_actions?.length;
}

function workerLeaseMatches(run, contracts, lease, receipt, resolved) {
  const identity = contracts.identities ?? {};
  const binding = receipt.extensions?.worker_lease_binding;
  const receiptIdentity = receipt.extensions?.identity_correlations;
  const acquiredAt = Date.parse(lease.acquired_at);
  const releasedAt = Date.parse(lease.released_at);
  if (lease.contract_version !== "atlas.worker-lease.v2" || lease.status !== "released") return false;
  if (lease.lease_id !== identity.leaseId || lease.job_id !== identity.jobId || lease.component_id !== identity.componentId) return false;
  if (lease.owner?.worker_id !== identity.workerId || lease.extensions?.run_id !== run.runId || lease.extensions?.execution_class !== identity.executionClass) return false;
  if (!Number.isFinite(acquiredAt) || !Number.isFinite(releasedAt) || releasedAt < acquiredAt) return false;
  if (lease.recovery?.strategy !== "release" || lease.extensions?.release_proven !== true) return false;
  if (lease.workspace?.root !== identity.workspace?.root || lease.workspace?.worktree !== identity.workspace?.worktree || lease.workspace?.branch !== identity.workspace?.branch) return false;
  if (receipt.correlations?.thread_id !== lease.owner?.thread_id || receipt.correlations?.turn_id !== lease.owner?.turn_id) return false;
  if (receipt.correlations?.branch !== lease.workspace?.branch || receipt.correlations?.worktree !== lease.workspace?.worktree) return false;
  if (receiptIdentity?.worker_id !== lease.owner?.worker_id || receiptIdentity?.workspace_root !== lease.workspace?.root || receiptIdentity?.execution_class !== lease.extensions?.execution_class) return false;
  if (!isRecord(binding) || binding.lease_id !== lease.lease_id || binding.status !== "released" || resolvedPath(binding.artifact_ref) !== resolved.workerLease) return false;
  if (!receipt.evidence_refs?.some((reference) => resolvedPath(reference) === resolved.workerLease)) return false;
  const resources = Array.isArray(lease.resources) ? lease.resources : [];
  if (lease.workspace?.worktree) {
    if (!resources.some((resource) => resource?.kind === "worktree" && resource.resource_id === lease.workspace.worktree && resource.exclusive === true)) return false;
  } else if (!resources.some((resource) => resource?.kind === "custom" && resource.resource_id === lease.workspace?.root && resource.exclusive === true)) return false;
  if (lease.workspace?.branch && !resources.some((resource) => resource?.kind === "branch" && resource.resource_id === lease.workspace.branch && resource.exclusive === true)) return false;
  return true;
}

export async function validateAdoption(runPath) {
  let run;
  try { run = await readJson(path.resolve(runPath)); } catch (error) {
    return fail("MALFORMED_JSON", [error instanceof SyntaxError ? "malformed JSON rejected" : "run input is unreadable"]);
  }
  if (!isRecord(run)) return fail("INVALID_RUN", ["run must be an object"]);

  const contracts = run.atlasContractsV2;
  const paths = contracts?.artifactPaths;
  const declaredFamilies = isRecord(paths) ? Object.keys(paths).sort() : [];
  if (declaredFamilies.length !== EXPECTED_FAMILIES.length || declaredFamilies.join(",") !== [...EXPECTED_FAMILIES].sort().join(",") || EXPECTED_FAMILIES.some((family) => typeof paths[family] !== "string")) {
    return fail("ARTIFACT_COUNT_MISMATCH", [`exactly ${EXPECTED_FAMILIES.length} declared artifacts are required`]);
  }

  const resolved = {};
  const pathErrors = [];
  for (const family of EXPECTED_FAMILIES) {
    const file = path.resolve(paths[family]);
    resolved[family] = file;
    if (!(file === ROOT || file.startsWith(`${ROOT}${path.sep}`))) pathErrors.push("escaped artifact path");
    try { if (await fs.realpath(file) !== file) pathErrors.push("artifact realpath mismatch"); } catch { pathErrors.push("artifact path does not exist"); }
  }
  if (new Set(Object.values(resolved)).size !== EXPECTED_FAMILIES.length) pathErrors.push("duplicate artifact path");
  if (pathErrors.length) return fail("UNSAFE_PATH", pathErrors);

  const artifacts = {};
  const validations = {};
  for (const family of EXPECTED_FAMILIES) {
    try { artifacts[family] = await readJson(resolved[family]); } catch { return fail("MALFORMED_JSON", ["malformed JSON rejected"]); }
    validations[family] = await validateArtifact(family, resolved[family]);
    if (!validations[family].result.ok) return fail("CANONICAL_SCHEMA_INVALID", [`${family} canonical schema validation failed`]);
  }
  for (const family of EXPECTED_FAMILIES) {
    if (!producerValidationMatches(contracts.validation?.[family], { family, ...validations[family] }, resolved[family])) {
      return fail("PRODUCER_VALIDATION_MISMATCH", [`${family} producer validation representation does not match canonical validation`]);
    }
  }

  const manifest = artifacts.componentManifest;
  const job = artifacts.jobEnvelope;
  const context = artifacts.contextPacket;
  const approval = artifacts.approvalRecord;
  const workerLease = artifacts.workerLease;
  const evidenceBundle = artifacts.evidenceBundle;
  const receipt = artifacts.executionReceipt;
  const identity = contracts.identities ?? {};

  if (identity.componentId !== manifest.component_id || job.component_id !== manifest.component_id || receipt.component_id !== manifest.component_id) return fail("COMPONENT_MISMATCH", ["component correlation mismatch"]);
  if (job.project_id !== receipt.project_id || job.project_id !== "atlas") return fail("PROJECT_MISMATCH", ["project correlation mismatch"]);
  if (identity.jobId !== job.job_id || receipt.job_id !== job.job_id) return fail("JOB_MISMATCH", ["job correlation mismatch"]);
  if (identity.runId !== run.runId || job.extensions?.run_id !== run.runId) return fail("RUN_MISMATCH", ["run correlation mismatch"]);
  if (context.job_id !== job.job_id || context.component_id !== manifest.component_id || context.extensions?.run_id !== run.runId) return fail("CONTEXT_CORRELATION_MISMATCH", ["ContextPacket job, component, or run correlation mismatch"]);
  if (approval.job_id !== job.job_id || approval.extensions?.component_id !== manifest.component_id || approval.extensions?.run_id !== run.runId) return fail("APPROVAL_CORRELATION_MISMATCH", ["ApprovalRecord job, component, or run correlation mismatch"]);
  if (evidenceBundle.job_id !== job.job_id || evidenceBundle.environment?.component_id !== manifest.component_id || evidenceBundle.extensions?.run_id !== run.runId) return fail("EVIDENCE_CORRELATION_MISMATCH", ["EvidenceBundle job, component, or run correlation mismatch"]);
  if (!workerLeaseMatches(run, contracts, workerLease, receipt, resolved)) return fail("WORKER_LEASE_MISMATCH", ["WorkerLease identity, resource, lifecycle, or receipt binding mismatch"]);
  if (!producerValidationMatches(contracts.validation?.workerLeaseTerminal, { family: "workerLease", ...validations.workerLease }, resolved.workerLease)) return fail("WORKER_LEASE_TERMINAL_VALIDATION_MISMATCH", ["WorkerLease terminal validation representation does not match canonical validation"]);
  const leaseBytes = await fs.readFile(resolved.workerLease);
  const leaseDigest = `sha256:${crypto.createHash("sha256").update(leaseBytes).digest("hex")}`;
  if (receipt.extensions?.worker_lease_binding?.digest !== leaseDigest || contracts.status?.leaseDigest !== leaseDigest || contracts.status?.lease !== "released") return fail("WORKER_LEASE_DIGEST_MISMATCH", ["WorkerLease digest or terminal status binding mismatch"]);
  if (!artifactReferencesMatch(receipt, resolved)) return fail("RECEIPT_ARTIFACT_REFERENCE_MISMATCH", ["ExecutionReceipt artifact references must exactly match declared artifacts"]);

  if (approval.decision !== "rejected") return fail("APPROVAL_DENIAL_MISMATCH", ["external mutation approval must be rejected"]);
  if (!authorityDenied(run, job, approval, receipt)) return fail("EXTERNAL_AUTHORITY_ACTION", ["external authority denial or no-action proof is missing"]);
  if (job.expected_receipt_version !== "atlas.execution-receipt.v2" || receipt.contract_version !== "atlas.execution-receipt.v2") return fail("RECEIPT_VERSION_MISMATCH", ["receipt version mismatch"]);
  if (!String(run.status ?? "").startsWith("success") || contracts.status?.preflight !== "validated" || !["success_no_changes", "succeeded"].includes(contracts.status?.terminal) || contracts.status?.receiptValidated !== true || receipt.status !== "succeeded" || run.verification?.some((entry) => entry?.exitCode !== 0)) return fail("TERMINAL_STATUS_MISMATCH", ["producer terminal status is not accepted"]);
  if (!hasTerminalVerificationEvidence(receipt, evidenceBundle) || !receipt.verification?.length || receipt.verification.some((entry) => entry?.status !== "passed")) return fail("TERMINAL_EVIDENCE_MISMATCH", ["terminal verification evidence is missing or failed"]);
  if (receipt.blockers?.length || run.proofGateFailureReason || run.runtimePolicy?.blockers?.length || contracts.status?.reasonCode) return fail("BLOCKER_PRESENT", ["producer or receipt blocker is present"]);
  if (!run.workerGitState || !Array.isArray(run.workerGitState.violations) || run.workerGitState.violations.length || run.workerGitState.failureCode) return fail("WORKER_GIT_VIOLATION", ["worker Git violation"]);

  const evidence = {};
  for (const family of EXPECTED_FAMILIES) {
    const bytes = await fs.readFile(resolved[family]);
    evidence[family] = { path: relative(resolved[family]), bytes: bytes.length, sha256: `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}` };
  }
  return { ok: true, code: "ACCEPTED", reasonCode: "ACCEPTED", families: EXPECTED_FAMILIES, runId: run.runId, jobId: job.job_id, evidence };
}

function parseArgs(argv) {
  const runIndex = argv.indexOf("--run");
  return {
    json: argv.includes("--json"),
    all: argv.includes("--all"),
    cardBoard: argv.includes("--card-board"),
    markerEvidence: argv.includes("--marker-evidence"),
    run: runIndex >= 0 ? argv[runIndex + 1] : null,
  };
}
const args = parseArgs(process.argv.slice(2));
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = args.all
    ? (args.run ? await validateAdoptedMesh(args.run) : fail("MISSING_INPUT", ["--run is required with --all"]))
    : args.cardBoard
      ? await validateCardBoardAdoption()
      : args.markerEvidence
        ? await validateMarkerEvidenceAdoption()
      : args.run
        ? await validateAdoption(args.run)
        : fail("MISSING_INPUT", ["--run, --card-board, --marker-evidence, or --all with --run is required"]);
  if (args.json) console.log(JSON.stringify(result));
  else console.log(`${result.code}: ${result.ok ? "Contracts v2 adoption accepted" : result.errors.join(" ")}`);
  process.exitCode = result.ok ? 0 : 1;
}
