import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ADOPTED_FAMILIES,
  CARD_BOARD_FAMILIES,
  EXPECTED_FAMILIES,
  buildCanonicalCardBoardEvidence,
  validateAdoptedMesh,
  validateAdoption,
  validateCardBoardAdoption,
  validateCardBoardArtifacts,
} from "./validate_contracts_v2_adoption.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const canary = path.join(ROOT, "repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/run.json");
const source = JSON.parse(await fs.readFile(canary, "utf8"));
const temp = await fs.mkdtemp(path.join(ROOT, "tmp", "atlas-contracts-v2-adoption-"));

function replacePath(value, from, to) { return typeof value === "string" ? value.replaceAll(from, to) : value; }

async function fixture(name, mutate = () => {}) {
  const directory = path.join(temp, name);
  await fs.mkdir(directory, { recursive: true });
  const run = structuredClone(source);
  const artifacts = {};
  const originalPaths = source.atlasContractsV2.artifactPaths;
  const artifactPaths = {};
  for (const family of EXPECTED_FAMILIES) {
    artifacts[family] = JSON.parse(await fs.readFile(originalPaths[family], "utf8"));
    artifactPaths[family] = path.join(directory, `${family}.json`);
  }
  const writePaths = { ...artifactPaths };
  run.atlasContractsV2.artifactPaths = artifactPaths;
  for (const family of EXPECTED_FAMILIES) {
    const producer = run.atlasContractsV2.validation[family];
    producer.artifactPath = artifactPaths[family];
    producer.result.artifact = artifactPaths[family];
    producer.stdout = `${JSON.stringify(producer.result)}\n`;
  }
  const terminalLeaseValidation = run.atlasContractsV2.validation.workerLeaseTerminal;
  terminalLeaseValidation.artifactPath = artifactPaths.workerLease;
  terminalLeaseValidation.result.artifact = artifactPaths.workerLease;
  terminalLeaseValidation.stdout = `${JSON.stringify(terminalLeaseValidation.result)}\n`;
  for (const key of ["contextPacket", "approvalRecord", "workerLease", "evidenceBundle"]) {
    const oldPath = originalPaths[key];
    const newPath = artifactPaths[key];
    artifacts.executionReceipt.evidence_refs = artifacts.executionReceipt.evidence_refs.map((entry) => replacePath(entry, oldPath, newPath));
    artifacts.executionReceipt.extensions.artifact_refs[{ contextPacket: "context_packet", approvalRecord: "approval_record", workerLease: "worker_lease", evidenceBundle: "evidence_bundle" }[key]] = newPath;
  }
  artifacts.executionReceipt.extensions.worker_lease_binding.artifact_ref = artifactPaths.workerLease;
  const workerLeaseBytes = Buffer.from(JSON.stringify(artifacts.workerLease));
  const workerLeaseDigest = `sha256:${crypto.createHash("sha256").update(workerLeaseBytes).digest("hex")}`;
  artifacts.executionReceipt.extensions.worker_lease_binding.digest = workerLeaseDigest;
  run.atlasContractsV2.status.leaseDigest = workerLeaseDigest;
  mutate({ run, artifacts, artifactPaths });
  for (const family of EXPECTED_FAMILIES) await fs.writeFile(writePaths[family], JSON.stringify(artifacts[family]));
  const runPath = path.join(directory, "run.json");
  await fs.writeFile(runPath, JSON.stringify(run));
  return runPath;
}

async function scenario(name, mutate, expected) {
  const result = await validateAdoption(await fixture(name, mutate));
  assert.equal(result.ok, false, `${name} must be rejected`);
  assert.equal(result.reasonCode, expected, `${name} reason code`);
}

let cardBoardSource;
async function cardBoardScenario(name, mutate, expected) {
  const card = structuredClone(cardBoardSource.card);
  const event = structuredClone(cardBoardSource.event);
  mutate({ card, event });
  const result = await validateCardBoardArtifacts(card, event);
  assert.equal(result.ok, false, `${name} must be rejected`);
  assert.equal(result.reasonCode, expected, `${name} reason code`);
}

try {
  const accepted = await validateAdoption(canary);
  assert.equal(accepted.code, "ACCEPTED");
  assert.deepEqual(accepted.families, EXPECTED_FAMILIES);
  assert.deepEqual(Object.keys(accepted.evidence), EXPECTED_FAMILIES);
  for (const family of EXPECTED_FAMILIES) {
    assert.match(accepted.evidence[family].path, /^repos\/_stack\//);
    assert.equal(accepted.evidence[family].sha256.startsWith("sha256:"), true);
    assert.equal(accepted.evidence[family].bytes > 0, true);
  }

  await scenario("job-mismatch", ({ run }) => { run.atlasContractsV2.identities.jobId = "wrong-job"; }, "JOB_MISMATCH");
  await scenario("context-job-mismatch", ({ artifacts }) => { artifacts.contextPacket.job_id = "wrong-job"; }, "CONTEXT_CORRELATION_MISMATCH");
  await scenario("approval-not-rejected", ({ artifacts }) => { artifacts.approvalRecord.decision = "approved"; }, "APPROVAL_DENIAL_MISMATCH");
  await scenario("evidence-job-mismatch", ({ artifacts }) => { artifacts.evidenceBundle.job_id = "wrong-job"; }, "EVIDENCE_CORRELATION_MISMATCH");
  await scenario("lease-job-mismatch", ({ artifacts }) => { artifacts.workerLease.job_id = "wrong-job"; }, "WORKER_LEASE_MISMATCH");
  await scenario("lease-active-terminal", ({ artifacts }) => { artifacts.workerLease.status = "active"; artifacts.workerLease.released_at = null; }, "WORKER_LEASE_MISMATCH");
  await scenario("lease-resource-mismatch", ({ artifacts }) => { artifacts.workerLease.resources[0].resource_id = "wrong-worktree"; }, "WORKER_LEASE_MISMATCH");
  await scenario("lease-terminal-validation", ({ run }) => { run.atlasContractsV2.validation.workerLeaseTerminal.schemaId = "atlas.job-envelope.v2"; }, "WORKER_LEASE_TERMINAL_VALIDATION_MISMATCH");
  await scenario("lease-digest-mismatch", ({ artifacts }) => { artifacts.executionReceipt.extensions.worker_lease_binding.digest = "sha256:0000000000000000000000000000000000000000000000000000000000000000"; }, "WORKER_LEASE_DIGEST_MISMATCH");
  await scenario("receipt-reference-mismatch", ({ artifacts }) => { artifacts.executionReceipt.extensions.artifact_refs.context_packet = artifacts.executionReceipt.extensions.artifact_refs.approval_record; }, "RECEIPT_ARTIFACT_REFERENCE_MISMATCH");
  await scenario("producer-validation-mismatch", ({ run }) => { run.atlasContractsV2.validation.evidenceBundle.schemaId = "atlas.job-envelope.v2"; }, "PRODUCER_VALIDATION_MISMATCH");
  await scenario("missing-artifact", ({ run }) => { delete run.atlasContractsV2.artifactPaths.evidenceBundle; }, "ARTIFACT_COUNT_MISMATCH");
  await scenario("extra-artifact", ({ run }) => { run.atlasContractsV2.artifactPaths.extraArtifact = run.atlasContractsV2.artifactPaths.evidenceBundle; }, "ARTIFACT_COUNT_MISMATCH");
  await scenario("duplicate-artifact", ({ run }) => { run.atlasContractsV2.artifactPaths.evidenceBundle = run.atlasContractsV2.artifactPaths.contextPacket; }, "UNSAFE_PATH");
  await scenario("escaped-path", ({ run }) => { run.atlasContractsV2.artifactPaths.jobEnvelope = "C:/Windows/job.json"; }, "UNSAFE_PATH");
  await scenario("failed-run", ({ run }) => { run.status = "failed"; }, "TERMINAL_STATUS_MISMATCH");
  await scenario("nonterminal-run", ({ run }) => { run.atlasContractsV2.status.terminal = "running"; }, "TERMINAL_STATUS_MISMATCH");
  await scenario("worker-git", ({ run }) => { run.workerGitState.violations = ["dirty"]; }, "WORKER_GIT_VIOLATION");
  await scenario("external-authority", ({ run }) => { run.authorityActions = ["push"]; }, "EXTERNAL_AUTHORITY_ACTION");
  await scenario("terminal-evidence", ({ artifacts }) => { artifacts.evidenceBundle.evidence[0].status = "failed"; }, "TERMINAL_EVIDENCE_MISMATCH");

  cardBoardSource = await buildCanonicalCardBoardEvidence();
  const cardBoardAccepted = await validateCardBoardAdoption();
  assert.equal(cardBoardAccepted.code, "ACCEPTED");
  assert.deepEqual(cardBoardAccepted.families, CARD_BOARD_FAMILIES);
  assert.deepEqual(Object.keys(cardBoardAccepted.evidence), CARD_BOARD_FAMILIES);
  assert.equal(cardBoardAccepted.receipt.status, "admitted_dry_run");
  assert.equal(cardBoardAccepted.receipt.card_record.project_id, "mazer");
  assert.equal(cardBoardAccepted.receipt.writer_boundary.writer_authority, "discordos");
  assert.equal(cardBoardAccepted.receipt.writer_boundary.sole_logical_writer, true);
  assert.equal(cardBoardAccepted.receipt.writer_boundary.external_mutation, false);
  assert.equal(cardBoardAccepted.receipt.writer_boundary.storage_applied, false);
  assert.equal(cardBoardAccepted.consumerGit.mergeCommit, "b2dbcc1a9ca66876e9c07ea8c6032701c9aaea2a");
  assert.equal(cardBoardAccepted.consumerGit.consumerFilesUnchanged, true);

  const meshAccepted = await validateAdoptedMesh(canary);
  assert.equal(meshAccepted.code, "ACCEPTED");
  assert.deepEqual(meshAccepted.families, ADOPTED_FAMILIES);
  assert.deepEqual(Object.keys(meshAccepted.evidence), ADOPTED_FAMILIES);
  assert.equal(meshAccepted.acceptedUnits, 9);
  assert.equal(meshAccepted.implementationFoundations, 11);
  assert.equal(meshAccepted.percentage, 82);

  await cardBoardScenario("card-schema-invalid", ({ card }) => { card.lifecycle = "doing"; }, "CARD_RECORD_SCHEMA_INVALID");
  await cardBoardScenario("card-project-mismatch", ({ card }) => { card.project_id = "other"; }, "CARD_RECORD_PROJECT_MISMATCH");
  await cardBoardScenario("event-schema-invalid", ({ event }) => { event.result.status = "live"; }, "BOARD_EVENT_SCHEMA_INVALID");
  await cardBoardScenario("event-card-mismatch", ({ event }) => { event.card_id = "other-card"; }, "BOARD_EVENT_CARD_MISMATCH");
  await cardBoardScenario("event-board-mismatch", ({ event }) => { event.board_id = "discordos:project-feedback:other"; }, "BOARD_EVENT_BOARD_MISMATCH");
  await cardBoardScenario("event-version-mismatch", ({ event }) => { event.expected_version -= 1; }, "BOARD_EVENT_VERSION_MISMATCH");
  await cardBoardScenario("event-from-state-mismatch", ({ event }) => { event.intent.from = "planning"; }, "BOARD_EVENT_FROM_STATE_MISMATCH");
  await cardBoardScenario("event-idempotency-mismatch", ({ event }) => { event.idempotency_key = "abk_00000000000000000000000000000000"; }, "BOARD_EVENT_IDEMPOTENCY_MISMATCH");
  await cardBoardScenario("event-identity-mismatch", ({ event }) => { event.event_id = "abe_00000000000000000000000000000000"; }, "BOARD_EVENT_IDENTITY_MISMATCH");
  await cardBoardScenario("event-writer-mismatch", ({ event }) => { event.extensions.writer_authority = "atlas"; }, "WRITER_AUTHORITY_MISMATCH");
  await cardBoardScenario("event-second-writer", ({ event }) => { event.extensions.second_writer = "atlas"; event.extensions.deploy_authority = "production"; }, "SECOND_WRITER_AUTHORITY");
  await cardBoardScenario("event-result-mismatch", ({ event }) => { event.result.observed_version = event.expected_version; event.result.readback_at = "2026-07-15T15:05:00Z"; event.result.receipt_ref = "runtime/receipts/board-event.json"; }, "BOARD_EVENT_RESULT_MISMATCH");

  const malformed = path.join(temp, "malformed.json");
  await fs.writeFile(malformed, "{ malformed JSON rejected");
  const malformedResult = await validateAdoption(malformed);
  assert.equal(malformedResult.reasonCode, "MALFORMED_JSON");
  console.log("real seven-artifact WorkerLease canary acceptance passed");
  console.log("Cluster 1 through Cluster 3 rejection scenarios: passed");
  console.log("independent CardRecord + BoardEvent consumer acceptance passed");
  console.log("Cluster 4 rejection scenarios: passed");
  console.log("Contracts Mesh calculation: 9/11 = 82%");
} finally {
  await fs.rm(temp, { recursive: true, force: true });
}
