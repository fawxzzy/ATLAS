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
assert.equal(control.cards[0].card_id, card.card_id);
assert.equal(control.cards[0].project_id, card.project_id);
assert.equal(control.cards[0].board_id, card.board_id);

console.log("ATLAS board authority contract tests passed.");
