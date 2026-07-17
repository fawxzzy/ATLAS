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
  assert.deepEqual(validateJsonSchema(valid, loaded.schema), [], `${contractId} valid schema fixture`);
  assert.deepEqual(validateContractSemantics(contractId, valid), [], `${contractId} valid semantic fixture`);

  const invalid = await loadJson(path.join(fixturesDir, plan.invalid));
  const firstErrors = [
    ...validateJsonSchema(invalid, loaded.schema),
    ...validateContractSemantics(contractId, invalid),
  ];
  const secondErrors = [
    ...validateJsonSchema(invalid, loaded.schema),
    ...validateContractSemantics(contractId, invalid),
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

const rollover = validArtifacts.get("atlas.rollover-manifest.v1");
const livePredecessorRollover = structuredClone(rollover);
livePredecessorRollover.predecessor_epoch.status = "active";
assert(validateContractSemantics("atlas.rollover-manifest.v1", livePredecessorRollover).some(
  (error) => error.includes("terminal receipt evidence"),
));

console.log("ATLAS board authority contract tests passed.");
