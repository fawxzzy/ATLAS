import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  MarkerEvidenceAdmissionError,
  buildMarkerAdmissionReceipt,
  parseArgs,
  stableStringify,
  verifyMarkerConsumerReceipt,
} from "../ops/atlas/marker_evidence_admission.mjs";
import { buildCanonicalMarkerEvidence } from "../ops/atlas/validate_contracts_v2_adoption.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const temp = await fs.mkdtemp(path.join(ROOT, "tmp", "marker-evidence-admission-test-"));
const producer = await buildCanonicalMarkerEvidence();

function bytes(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function writeInputs(name, mutate = () => {}) {
  const directory = path.join(temp, name);
  await fs.mkdir(directory, { recursive: true });
  const marker = structuredClone(producer.marker);
  const job = structuredClone(producer.job);
  const executionReceipt = structuredClone(producer.executionReceipt);
  mutate({ marker, job, executionReceipt });
  const markerPath = path.join(directory, "marker-evidence.json");
  const jobPath = path.join(directory, "job-envelope.json");
  const executionReceiptPath = path.join(directory, "execution-receipt.json");
  await Promise.all([
    fs.writeFile(markerPath, bytes(marker)),
    fs.writeFile(jobPath, bytes(job)),
    fs.writeFile(executionReceiptPath, bytes(executionReceipt)),
  ]);
  return { markerPath, jobPath, executionReceiptPath };
}

async function expectRejection(name, mutate, reasonCode) {
  const inputs = await writeInputs(name, mutate);
  await assert.rejects(
    buildMarkerAdmissionReceipt(inputs),
    (error) => error instanceof MarkerEvidenceAdmissionError && error.reasonCode === reasonCode,
  );
}

test.after(async () => {
  await fs.rm(temp, { recursive: true, force: true });
});

test("emits a deterministic read-only receipt with stable input and result identity", async () => {
  const inputs = await writeInputs("accepted");
  const first = await buildMarkerAdmissionReceipt(inputs);
  const second = await buildMarkerAdmissionReceipt(inputs);
  assert.equal(stableStringify(first), stableStringify(second));
  assert.match(first.receipt_id, /^amer_[a-f0-9]{32}$/);
  assert.match(first.result_identity.result_id, /^ameres_[a-f0-9]{32}$/);
  assert.equal(first.status, "accepted_read_only");
  assert.equal(first.result_identity.numerator, 11);
  assert.equal(first.result_identity.denominator, 11);
  assert.equal(first.result_identity.percentage, 100);
  assert.equal(first.schema_source.schema_id, "atlas.marker-evidence.v2");
  assert.equal(first.authority.external_mutation, false);
  assert.equal(first.authority.marker_mutation, false);
  assert.equal(first.authority.parent_marker_movement, false);
});

test("rejects percentage and rounded-math drift", async () => {
  await expectRejection("percentage-mismatch", ({ marker }) => { marker.percentage = 99; }, "MARKER_PERCENTAGE_MISMATCH");
});

test("rejects transition drift", async () => {
  await expectRejection("transition-mismatch", ({ marker }) => { marker.transition.current_percentage = 99; }, "MARKER_TRANSITION_MISMATCH");
});

test("rejects stale evidence", async () => {
  await expectRejection("stale", ({ marker }) => { marker.freshness.status = "stale"; }, "MARKER_STALE");
});

test("rejects scope identity drift", async () => {
  await expectRejection("scope-mismatch", ({ marker }) => { marker.scope = "Accepted percentages without fixed identity."; }, "MARKER_SCOPE_MISMATCH");
});

test("rejects execution receipt correlation drift", async () => {
  await expectRejection("receipt-mismatch", ({ executionReceipt }) => { executionReceipt.job_id = "job-other"; }, "MARKER_RECEIPT_MISMATCH");
});

test("rejects missing independent consumer receipt", async () => {
  const inputs = await writeInputs("missing-consumer-receipt");
  const expected = await buildMarkerAdmissionReceipt(inputs);
  assert.throws(
    () => verifyMarkerConsumerReceipt(null, expected),
    (error) => error instanceof MarkerEvidenceAdmissionError && error.reasonCode === "MARKER_CONSUMER_RECEIPT_MISSING",
  );
});

test("rejects rollup identity drift", async () => {
  await expectRejection("rollup-mismatch", ({ marker }) => { marker.rollup_policy = "independent"; }, "MARKER_ROLLUP_MISMATCH");
});

test("rejects incomplete evidence lineage", async () => {
  await expectRejection("evidence-mismatch", ({ marker }) => { marker.evidence_refs.pop(); }, "MARKER_EVIDENCE_REF_MISMATCH");
});

test("rejects every mutation-oriented command flag", () => {
  for (const flag of ["--apply", "--write", "--ratchet", "--live", "--send", "--discord", "--deploy", "--production", "--prod"]) {
    assert.throws(
      () => parseArgs(["--marker", "marker.json", "--job", "job.json", "--receipt", "receipt.json", flag]),
      (error) => error instanceof MarkerEvidenceAdmissionError && error.reasonCode === "MARKER_MUTATION_NOT_ADMITTED",
      flag,
    );
  }
});
