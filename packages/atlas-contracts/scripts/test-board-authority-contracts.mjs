import assert from "node:assert/strict";
import path from "node:path";
import {
  fixturesDir,
  knownSchemaPlan,
  loadJson,
  loadKnownSchema,
  validateJsonSchema,
} from "./lib/validate-json-schema.mjs";
import { validateContractSemantics } from "./lib/validate-semantics.mjs";
import {
  COMMIT_CLOSURE_ORDER,
  TARGET_CONTRACTS,
  validateProjectionAckAgainstDelivery,
} from "./lib/validate-board-authority.mjs";

const contractIds = Object.freeze([
  "atlas.card-record.v3",
  "atlas.card-event.v3",
  "atlas.board-commit-receipt.v1",
  "atlas.projection-delivery.v1",
  "atlas.projection-ack.v1",
  "atlas.board-authority-migration.v1",
  "atlas.control-board-read-model.v1",
  "atlas.rollover-manifest.v1",
]);
const validArtifacts = new Map();

for (const contractId of contractIds) {
  const plan = knownSchemaPlan.find((candidate) => candidate.id === contractId);
  assert(plan, `${contractId} must be registered`);
  const loaded = await loadKnownSchema(contractId);
  assert.equal(loaded.ok, true);
  assert.equal(loaded.schema.$schema, "https://json-schema.org/draft/2020-12/schema");

  const valid = await loadJson(path.join(fixturesDir, plan.valid));
  validArtifacts.set(contractId, valid);
  const semanticContext = contractId === "atlas.projection-ack.v1"
    ? { projectionDelivery: validArtifacts.get("atlas.projection-delivery.v1") }
    : {};
  assert.deepEqual(validateJsonSchema(valid, loaded.schema), [], `${contractId} valid schema fixture`);
  assert.deepEqual(validateContractSemantics(contractId, valid, semanticContext), [], `${contractId} valid semantic fixture`);

  const invalid = await loadJson(path.join(fixturesDir, plan.invalid));
  const firstErrors = [
    ...validateJsonSchema(invalid, loaded.schema),
    ...validateContractSemantics(contractId, invalid, semanticContext),
  ];
  const secondErrors = [
    ...validateJsonSchema(invalid, loaded.schema),
    ...validateContractSemantics(contractId, invalid, semanticContext),
  ];
  assert(firstErrors.length > 0, `${contractId} invalid fixture must fail`);
  assert.deepEqual(firstErrors, secondErrors, `${contractId} errors must be deterministic`);
}

assert.deepEqual(COMMIT_CLOSURE_ORDER, [
  "validate-execution-receipt",
  "idempotency-lookup",
  "expected-version-cas",
  "append-card-event",
  "materialize-card-record",
  "enqueue-projection-delivery",
  "persist-board-commit-receipt",
  "commit-transaction",
]);
assert.deepEqual(TARGET_CONTRACTS, contractIds);

const card = validArtifacts.get("atlas.card-record.v3");
const event = validArtifacts.get("atlas.card-event.v3");
const commit = validArtifacts.get("atlas.board-commit-receipt.v1");
const delivery = validArtifacts.get("atlas.projection-delivery.v1");
const ack = validArtifacts.get("atlas.projection-ack.v1");
const control = validArtifacts.get("atlas.control-board-read-model.v1");
const migrationSchema = await loadKnownSchema("atlas.board-authority-migration.v1");
const eventSchema = await loadKnownSchema("atlas.card-event.v3");
const deliverySchema = await loadKnownSchema("atlas.projection-delivery.v1");
const ackSchema = await loadKnownSchema("atlas.projection-ack.v1");
const rolloverSchema = await loadKnownSchema("atlas.rollover-manifest.v1");

async function assertSemanticNegative(contractId, schema, fixtureRef, context = {}) {
  const artifact = await loadJson(path.join(fixturesDir, fixtureRef));
  assert.deepEqual(validateJsonSchema(artifact, schema), [], `${fixtureRef} must remain schema-valid`);
  const firstErrors = validateContractSemantics(contractId, artifact, context);
  const secondErrors = validateContractSemantics(contractId, artifact, context);
  assert(firstErrors.length > 0, `${fixtureRef} must fail semantic validation`);
  assert.deepEqual(firstErrors, secondErrors, `${fixtureRef} semantic errors must be deterministic`);
  return firstErrors;
}
for (const artifact of [event, commit, delivery, ack]) {
  assert.equal(artifact.card_id, card.card_id);
  assert.equal(artifact.project_id, card.project_id);
  assert.equal(artifact.board_id, card.board_id);
  assert.equal(artifact.card_version, card.version);
}
assert.equal(event.resulting_record_digest, commit.card_record_digest);
assert.equal(event.projection_delivery_id, delivery.delivery_id);
assert.equal(event.commit_receipt_id, commit.receipt_id);
assert.equal(commit.projection_delivery_id, delivery.delivery_id);
assert.equal(delivery.event_id, event.event_id);
assert.equal(delivery.event_sequence, event.event_sequence);
assert.equal(ack.delivery_id, delivery.delivery_id);
assert.equal(ack.event_id, event.event_id);
assert.equal(ack.payload_digest, delivery.payload_digest);
assert.deepEqual(validateProjectionAckAgainstDelivery(ack, delivery), []);
const mismatchedAck = structuredClone(ack);
mismatchedAck.payload_digest = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
assert.deepEqual(validateProjectionAckAgainstDelivery(mismatchedAck, delivery), [
  "ProjectionAck $.payload_digest must equal ProjectionDelivery $.payload_digest",
]);
assert(validateContractSemantics("atlas.projection-ack.v1", mismatchedAck, { projectionDelivery: delivery }).some(
  (error) => error.includes("payload_digest"),
));
assert.equal(control.cards[0].card_id, card.card_id);
assert.equal(control.cards[0].project_id, card.project_id);
assert.equal(control.cards[0].board_id, card.board_id);

const mismatchedEpochEvent = structuredClone(event);
mismatchedEpochEvent.changes.set.epoch_id = "different-epoch";
assert(validateContractSemantics("atlas.card-event.v3", mismatchedEpochEvent).includes(
  "$.changes.set.epoch_id must equal $.epoch_id",
));

const migration = validArtifacts.get("atlas.board-authority-migration.v1");
const prematureActiveMigration = structuredClone(migration);
prematureActiveMigration.phase = "v3-active";
prematureActiveMigration.cutover.status = "active";
assert(validateContractSemantics("atlas.board-authority-migration.v1", prematureActiveMigration).some(
  (error) => error.includes("Migration phase v3-active is inconsistent"),
));
const activeMigration = structuredClone(migration);
activeMigration.phase = "v3-active";
activeMigration.v2_authority_snapshot = {
  status: "available",
  snapshot_id: "snapshot-v2",
  digest: "sha256:6666666666666666666666666666666666666666666666666666666666666666",
  captured_at: "2026-07-17T12:00:00Z",
  unknown_reason: null,
};
activeMigration.one_time_import = {
  ...activeMigration.one_time_import,
  status: "verified",
  source_snapshot_digest: activeMigration.v2_authority_snapshot.digest,
  event_sequence_start: 1,
  event_sequence_end: 20,
  imported_at: "2026-07-17T12:05:00Z",
};
activeMigration.first_v3_acceptance = {
  status: "accepted",
  receipt_id: "board-commit-first-v3",
  accepted_at: "2026-07-17T12:06:00Z",
};
activeMigration.rollback.current_mode = "v3-restore-replay-only";
activeMigration.cutover.status = "active";
assert.deepEqual(validateContractSemantics("atlas.board-authority-migration.v1", activeMigration), []);

for (const fixtureRef of [
  "valid/board-authority-migration.v1.import-failed.json",
  "valid/board-authority-migration.v1.import-unknown.json",
]) {
  const artifact = await loadJson(path.join(fixturesDir, fixtureRef));
  assert.deepEqual(validateJsonSchema(artifact, migrationSchema.schema), []);
  assert.deepEqual(validateContractSemantics("atlas.board-authority-migration.v1", artifact), []);
}

const lifecycleErrors = await assertSemanticNegative(
  "atlas.card-event.v3",
  eventSchema.schema,
  "invalid/card-event.v3.lifecycle-conflict.json",
);
assert(lifecycleErrors.some((error) => error.includes("set.lifecycle")));
const staleErrors = await assertSemanticNegative(
  "atlas.projection-delivery.v1",
  deliverySchema.schema,
  "invalid/projection-delivery.v1.stale-without-evidence.json",
);
assert(staleErrors.some((error) => error.includes("observed_at and response_digest")));
const ackCorrelationErrors = await assertSemanticNegative(
  "atlas.projection-ack.v1",
  ackSchema.schema,
  "invalid/projection-ack.v1.mismatched-delivery.json",
  { projectionDelivery: delivery },
);
assert(ackCorrelationErrors.some((error) => error.includes("payload_digest")));
const migrationPhaseErrors = await assertSemanticNegative(
  "atlas.board-authority-migration.v1",
  migrationSchema.schema,
  "invalid/board-authority-migration.v1.failed-phase-mismatch.json",
);
assert(migrationPhaseErrors.some((error) => error.includes("Migration phase planned is inconsistent")));
const terminalReceiptErrors = await assertSemanticNegative(
  "atlas.rollover-manifest.v1",
  rolloverSchema.schema,
  "invalid/rollover-manifest.v1.unrelated-terminal-receipt.json",
);
assert(terminalReceiptErrors.some((error) => error.includes("identified terminal receipt")));

const rollover = validArtifacts.get("atlas.rollover-manifest.v1");
const livePredecessorRollover = structuredClone(rollover);
livePredecessorRollover.predecessor_epoch.status = "active";
assert(validateContractSemantics("atlas.rollover-manifest.v1", livePredecessorRollover).some(
  (error) => error.includes("identified terminal receipt"),
));

console.log("ATLAS board authority contract tests passed.");
