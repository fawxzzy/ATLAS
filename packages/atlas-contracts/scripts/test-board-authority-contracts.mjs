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
  projectInitialCardRecordV3,
  validateCardRecordV3,
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
const cardSchema = await loadKnownSchema("atlas.card-record.v3");
const migrationSchema = await loadKnownSchema("atlas.board-authority-migration.v1");
const eventSchema = await loadKnownSchema("atlas.card-event.v3");
const deliverySchema = await loadKnownSchema("atlas.projection-delivery.v1");
const ackSchema = await loadKnownSchema("atlas.projection-ack.v1");
const rolloverSchema = await loadKnownSchema("atlas.rollover-manifest.v1");
const controlSchema = await loadKnownSchema("atlas.control-board-read-model.v1");

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
const projectedInitialCard = projectInitialCardRecordV3(event);
assert.deepEqual(validateJsonSchema(projectedInitialCard, cardSchema.schema), []);
assert.deepEqual(validateCardRecordV3(projectedInitialCard), []);

for (const fixtureRef of [
  "valid/card-event.v3.initial-standing-anchor.json",
  "valid/card-event.v3.archive-materialization.json",
  "valid/card-event.v3.archive-exit-materialization.json",
  "valid/card-event.v3.partial-archive-state.json",
]) {
  const artifact = await loadJson(path.join(fixturesDir, fixtureRef));
  assert.deepEqual(validateJsonSchema(artifact, eventSchema.schema), [], `${fixtureRef} schema`);
  assert.deepEqual(validateContractSemantics("atlas.card-event.v3", artifact), [], `${fixtureRef} semantics`);
  if (artifact.event_type === "create" || artifact.event_type === "baseline-import") {
    const projected = projectInitialCardRecordV3(artifact);
    assert.deepEqual(validateJsonSchema(projected, cardSchema.schema), [], `${fixtureRef} CardRecord projection schema`);
    assert.deepEqual(validateCardRecordV3(projected), [], `${fixtureRef} CardRecord projection semantics`);
    if (fixtureRef.endsWith("initial-standing-anchor.json")) {
      assert.equal(projected.receipt_refs[0].status, "succeeded");
      assert.equal(projected.receipt_refs[1].status, "UNKNOWN");
    }
  }
}

const omitted = Symbol("omitted");
const archiveTransitionTemplate = await loadJson(path.join(
  fixturesDir,
  "valid/card-event.v3.archive-materialization.json",
));
const archiveTransitionCases = [
  { label: "enter archived with full post-state", from: "review", to: "archived", archiveState: "archived", standingAnchor: false, valid: true },
  { label: "enter archived without archive_state", from: "review", to: "archived", archiveState: omitted, standingAnchor: false, error: "crossing the archived boundary" },
  { label: "enter archived with non-archived state", from: "review", to: "archived", archiveState: "active", standingAnchor: false, error: "archive_state archived must move together" },
  { label: "enter archived without standing-anchor post-state", from: "review", to: "archived", archiveState: "archived", standingAnchor: omitted, error: "explicit $.changes.set.standing_anchor false" },
  { label: "enter archived as standing anchor", from: "review", to: "archived", archiveState: "archived", standingAnchor: true, error: "Stable standing anchors" },
  { label: "leave archived to active", from: "archived", to: "review", archiveState: "active", standingAnchor: omitted, valid: true },
  { label: "leave archived to successor-pending", from: "archived", to: "review", archiveState: "successor-pending", standingAnchor: omitted, valid: true },
  { label: "leave archived to archive-eligible", from: "archived", to: "review", archiveState: "archive-eligible", standingAnchor: omitted, valid: true },
  { label: "leave archived without archive_state", from: "archived", to: "review", archiveState: omitted, standingAnchor: omitted, error: "crossing the archived boundary" },
  { label: "leave archived with archived state", from: "archived", to: "review", archiveState: "archived", standingAnchor: omitted, error: "archive_state archived must move together" },
  { label: "stay outside archived without archive_state", from: "review", to: "completed", archiveState: omitted, standingAnchor: omitted, valid: true },
  { label: "stay outside archived with active state", from: "review", to: "completed", archiveState: "active", standingAnchor: omitted, valid: true },
  { label: "stay outside archived with successor-pending", from: "review", to: "completed", archiveState: "successor-pending", standingAnchor: omitted, valid: true },
  { label: "stay outside archived with archive-eligible", from: "review", to: "completed", archiveState: "archive-eligible", standingAnchor: omitted, valid: true },
  { label: "stay outside archived with archived state", from: "review", to: "completed", archiveState: "archived", standingAnchor: omitted, error: "archive_state archived must move together" },
  { label: "stay outside archived as standing anchor", from: "review", to: "completed", archiveState: omitted, standingAnchor: true, valid: true },
  { label: "stay archived without restating archive_state", from: "archived", to: "archived", archiveState: omitted, standingAnchor: omitted, valid: true },
  { label: "stay archived with archived state", from: "archived", to: "archived", archiveState: "archived", standingAnchor: false, valid: true },
  { label: "stay archived with non-archived state", from: "archived", to: "archived", archiveState: "active", standingAnchor: false, error: "archive_state archived must move together" },
];
for (const testCase of archiveTransitionCases) {
  const candidate = structuredClone(archiveTransitionTemplate);
  candidate.event_type = "transition";
  candidate.changes.set = {};
  candidate.changes.transition = { from: testCase.from, to: testCase.to };
  if (testCase.archiveState !== omitted) candidate.changes.set.archive_state = testCase.archiveState;
  if (testCase.standingAnchor !== omitted) candidate.changes.set.standing_anchor = testCase.standingAnchor;
  assert.deepEqual(validateJsonSchema(candidate, eventSchema.schema), [], `${testCase.label} schema`);
  const errors = validateContractSemantics("atlas.card-event.v3", candidate);
  if (testCase.valid) {
    assert.deepEqual(errors, [], testCase.label);
  } else {
    assert(errors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${errors.join(" | ")}`);
  }
}

const receiptCases = [
  { label: "execution receipt absent from materialized refs", receipts: [], valid: true, statuses: [] },
  {
    label: "execution receipt identity and digest match",
    receipts: [{ receipt_id: event.execution_receipt.receipt_id, digest: event.execution_receipt.digest }],
    valid: true,
    statuses: ["succeeded"],
  },
  {
    label: "execution receipt identity matches but digest conflicts",
    receipts: [{ receipt_id: event.execution_receipt.receipt_id, digest: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }],
    error: "identity and digest",
    statuses: ["UNKNOWN"],
  },
  {
    label: "different receipt identity with execution digest",
    receipts: [{ receipt_id: "other-receipt", digest: event.execution_receipt.digest }],
    valid: true,
    statuses: ["UNKNOWN"],
  },
  {
    label: "different receipt identity and digest",
    receipts: [{ receipt_id: "other-receipt", digest: "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" }],
    valid: true,
    statuses: ["UNKNOWN"],
  },
];
for (const testCase of receiptCases) {
  const candidate = structuredClone(event);
  candidate.changes.add_receipts = structuredClone(testCase.receipts);
  assert.deepEqual(validateJsonSchema(candidate, eventSchema.schema), [], `${testCase.label} schema`);
  const errors = validateContractSemantics("atlas.card-event.v3", candidate);
  if (testCase.valid) {
    assert.deepEqual(errors, [], testCase.label);
  } else {
    assert(errors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${errors.join(" | ")}`);
  }
  const projected = projectInitialCardRecordV3(candidate);
  assert.deepEqual(validateJsonSchema(projected, cardSchema.schema), [], `${testCase.label} projection schema`);
  assert.deepEqual(projected.receipt_refs.map((receipt) => receipt.status), testCase.statuses, `${testCase.label} statuses`);
}

const eventVersionTemplate = await loadJson(path.join(
  fixturesDir,
  "valid/card-event.v3.partial-archive-state.json",
));
const eventVersionCases = [
  { label: "non-initial version one preimage", expectedVersion: 1, cardVersion: 2, eventSequence: 2, valid: true },
  { label: "non-initial version zero preimage", expectedVersion: 0, cardVersion: 1, eventSequence: 1, error: "expected_version >= 1" },
  { label: "event sequence equal to card version", expectedVersion: 1, cardVersion: 2, eventSequence: 2, valid: true },
  { label: "event sequence ahead of card version", expectedVersion: 1, cardVersion: 2, eventSequence: 3, valid: true },
  { label: "event sequence behind card version", expectedVersion: 1, cardVersion: 2, eventSequence: 1, error: "cannot precede $.card_version" },
];
for (const testCase of eventVersionCases) {
  const candidate = structuredClone(eventVersionTemplate);
  candidate.expected_version = testCase.expectedVersion;
  candidate.card_version = testCase.cardVersion;
  candidate.event_sequence = testCase.eventSequence;
  assert.deepEqual(validateJsonSchema(candidate, eventSchema.schema), [], `${testCase.label} schema`);
  const errors = validateContractSemantics("atlas.card-event.v3", candidate);
  if (testCase.valid) {
    assert.deepEqual(errors, [], testCase.label);
  } else {
    assert(errors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${errors.join(" | ")}`);
  }
}

function makeControlIdentityCase(secondCard) {
  const candidate = structuredClone(control);
  if (secondCard !== null) {
    candidate.cards.push({ ...structuredClone(candidate.cards[0]), ...secondCard });
    candidate.card_count = 2;
    candidate.projection_summary.queued = 2;
  }
  return candidate;
}
const controlIdentityCases = [
  { label: "single generated card identity", secondCard: null, valid: true },
  { label: "exact duplicate generated card identity", secondCard: {}, error: "duplicate identity" },
  { label: "same card ID in another board", secondCard: { board_id: "another-board" }, valid: true },
  { label: "same card ID in another project", secondCard: { project_id: "another-project" }, valid: true },
  { label: "different card ID in same project and board", secondCard: { card_id: "ATLAS-BOARD-001" }, valid: true },
];
for (const testCase of controlIdentityCases) {
  const candidate = makeControlIdentityCase(testCase.secondCard);
  assert.deepEqual(validateJsonSchema(candidate, controlSchema.schema), [], `${testCase.label} schema`);
  const errors = validateContractSemantics("atlas.control-board-read-model.v1", candidate);
  if (testCase.valid) {
    assert.deepEqual(errors, [], testCase.label);
  } else {
    assert(errors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${errors.join(" | ")}`);
  }
}

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
const invalidTransitionTarget = await loadJson(path.join(
  fixturesDir,
  "invalid/card-event.v3.invalid-transition-target.json",
));
const invalidTransitionTargetErrors = validateJsonSchema(invalidTransitionTarget, eventSchema.schema);
assert(invalidTransitionTargetErrors.some((error) => error.includes("changes.transition.to")));
const nullTransitionFromErrors = await assertSemanticNegative(
  "atlas.card-event.v3",
  eventSchema.schema,
  "invalid/card-event.v3.null-transition-from.json",
);
assert(nullTransitionFromErrors.some((error) => error.includes("Non-initial transitions require")));
const ambiguousOperationErrors = await assertSemanticNegative(
  "atlas.card-event.v3",
  eventSchema.schema,
  "invalid/card-event.v3.ambiguous-operations.json",
);
for (const expected of [
  "duplicate blocker_id blocker-1",
  "duplicate resource_id resource-1",
  "duplicate receipt_id receipt-1",
  "add and remove blocker_id blocker-1",
  "add and remove resource_id resource-1",
]) {
  assert(ambiguousOperationErrors.some((error) => error.includes(expected)));
}
const initialMaterializationErrors = await assertSemanticNegative(
  "atlas.card-event.v3",
  eventSchema.schema,
  "invalid/card-event.v3.invalid-initial-materialization.json",
);
assert(initialMaterializationErrors.some((error) => error.includes("Stable standing anchors")));
const invalidInitialEvent = await loadJson(path.join(
  fixturesDir,
  "invalid/card-event.v3.invalid-initial-materialization.json",
));
const invalidInitialProjection = projectInitialCardRecordV3(invalidInitialEvent);
assert.deepEqual(validateJsonSchema(invalidInitialProjection, cardSchema.schema), []);
assert(validateCardRecordV3(invalidInitialProjection).some((error) => error.includes("Stable standing anchors")));
const updateMaterializationErrors = await assertSemanticNegative(
  "atlas.card-event.v3",
  eventSchema.schema,
  "invalid/card-event.v3.invalid-update-materialization.json",
);
assert(updateMaterializationErrors.some((error) => error.includes("archive_state archived must move together")));
for (const [fixtureRef, expectedError] of [
  ["invalid/card-event.v3.archive-entry-missing-state.json", "crossing the archived boundary"],
  ["invalid/card-event.v3.archive-entry-missing-standing-anchor.json", "explicit $.changes.set.standing_anchor false"],
  ["invalid/card-event.v3.archive-exit-missing-state.json", "crossing the archived boundary"],
  ["invalid/card-event.v3.execution-receipt-digest-mismatch.json", "identity and digest"],
  ["invalid/card-event.v3.non-initial-zero-version.json", "expected_version >= 1"],
  ["invalid/card-event.v3.sequence-before-version.json", "cannot precede $.card_version"],
]) {
  const fixtureErrors = await assertSemanticNegative("atlas.card-event.v3", eventSchema.schema, fixtureRef);
  assert(fixtureErrors.some((error) => error.includes(expectedError)));
}
const staleErrors = await assertSemanticNegative(
  "atlas.projection-delivery.v1",
  deliverySchema.schema,
  "invalid/projection-delivery.v1.stale-without-evidence.json",
);
assert(staleErrors.some((error) => error.includes("observed_at and response_digest")));
const availableUnknownErrors = await assertSemanticNegative(
  "atlas.projection-delivery.v1",
  deliverySchema.schema,
  "invalid/projection-delivery.v1.available-unknown-conflict.json",
);
assert(availableUnknownErrors.some((error) => error.includes("Available UNKNOWN projection")));
const appliedDeliveryRetryErrors = await assertSemanticNegative(
  "atlas.projection-delivery.v1",
  deliverySchema.schema,
  "invalid/projection-delivery.v1.applied-retry.json",
);
assert(appliedDeliveryRetryErrors.some((error) => error.includes("must be non-retryable")));
for (const fixtureRef of [
  "invalid/projection-delivery.v1.applied-zero-attempt.json",
  "invalid/projection-delivery.v1.stale-zero-attempt.json",
  "invalid/projection-delivery.v1.failed-zero-attempt.json",
  "invalid/projection-delivery.v1.available-unknown-zero-attempt.json",
]) {
  const attemptErrors = await assertSemanticNegative(
    "atlas.projection-delivery.v1",
    deliverySchema.schema,
    fixtureRef,
  );
  assert(attemptErrors.some((error) => error.includes("positive attempt_count")));
}
const unavailableUnknownZeroAttempt = await loadJson(path.join(
  fixturesDir,
  "valid/projection-delivery.v1.unavailable-unknown-zero-attempt.json",
));
assert.deepEqual(validateJsonSchema(unavailableUnknownZeroAttempt, deliverySchema.schema), []);
assert.deepEqual(validateContractSemantics("atlas.projection-delivery.v1", unavailableUnknownZeroAttempt), []);
const missingAvailabilityError = await assertSemanticNegative(
  "atlas.projection-delivery.v1",
  deliverySchema.schema,
  "invalid/projection-delivery.v1.unavailable-unknown-missing-error.json",
);
assert(missingAvailabilityError.some((error) => error.includes("availability error evidence")));

const projectionEvidenceTimestamp = "2026-07-17T12:01:00Z";
const projectionResponseDigest = "sha256:5555555555555555555555555555555555555555555555555555555555555555";
function makeProjectionDeliveryCase({ availability, state, ...overrides }) {
  const candidate = structuredClone(delivery);
  const unavailable = availability === "unavailable";
  const queued = state === "queued";
  const retryable = state !== "applied";
  candidate.availability = availability;
  candidate.state = state;
  candidate.retry = {
    attempt_count: unavailable || queued ? 0 : 1,
    retryable,
    next_attempt_at: retryable ? "2026-07-17T12:05:00Z" : null,
  };
  candidate.touched_card_readback = {
    mode: "exact-touched-card",
    card_id: candidate.card_id,
    state: unavailable ? "UNKNOWN" : state,
    request_count: unavailable ? null : (queued ? 0 : 1),
    full_scan: false,
    observed_at: unavailable || queued ? null : projectionEvidenceTimestamp,
    response_digest: unavailable || queued ? null : projectionResponseDigest,
  };
  candidate.last_error = unavailable || state === "failed" ? { code: "PROJECTION_ERROR" } : null;
  if (Object.hasOwn(overrides, "attemptCount")) candidate.retry.attempt_count = overrides.attemptCount;
  if (Object.hasOwn(overrides, "retryable")) candidate.retry.retryable = overrides.retryable;
  if (Object.hasOwn(overrides, "nextAttemptAt")) candidate.retry.next_attempt_at = overrides.nextAttemptAt;
  if (Object.hasOwn(overrides, "readbackState")) candidate.touched_card_readback.state = overrides.readbackState;
  if (Object.hasOwn(overrides, "requestCount")) candidate.touched_card_readback.request_count = overrides.requestCount;
  if (Object.hasOwn(overrides, "observedAt")) candidate.touched_card_readback.observed_at = overrides.observedAt;
  if (Object.hasOwn(overrides, "responseDigest")) candidate.touched_card_readback.response_digest = overrides.responseDigest;
  if (Object.hasOwn(overrides, "lastError")) candidate.last_error = overrides.lastError;
  if (overrides.omitLastError) delete candidate.last_error;
  return candidate;
}

const projectionDeliveryCases = [
  { label: "available queued", availability: "available", state: "queued", valid: true },
  { label: "available applied", availability: "available", state: "applied", valid: true },
  { label: "available stale retryable", availability: "available", state: "stale", valid: true },
  { label: "available stale terminal", availability: "available", state: "stale", retryable: false, nextAttemptAt: null, valid: true },
  { label: "available failed retryable", availability: "available", state: "failed", valid: true },
  { label: "available failed terminal", availability: "available", state: "failed", retryable: false, nextAttemptAt: null, valid: true },
  { label: "available UNKNOWN retryable", availability: "available", state: "UNKNOWN", valid: true },
  { label: "available UNKNOWN terminal", availability: "available", state: "UNKNOWN", retryable: false, nextAttemptAt: null, valid: true },
  { label: "unavailable UNKNOWN retryable", availability: "unavailable", state: "UNKNOWN", valid: true },
  { label: "unavailable UNKNOWN terminal", availability: "unavailable", state: "UNKNOWN", retryable: false, nextAttemptAt: null, valid: true },
  { label: "unavailable queued", availability: "unavailable", state: "queued", error: "must remain UNKNOWN" },
  { label: "unavailable applied", availability: "unavailable", state: "applied", error: "must remain UNKNOWN" },
  { label: "unavailable stale", availability: "unavailable", state: "stale", error: "must remain UNKNOWN" },
  { label: "unavailable failed", availability: "unavailable", state: "failed", error: "must remain UNKNOWN" },
  { label: "queued with positive attempt", availability: "available", state: "queued", attemptCount: 1, error: "attempt_count 0" },
  { label: "queued made non-retryable", availability: "available", state: "queued", retryable: false, nextAttemptAt: null, error: "must remain retryable" },
  { label: "queued with performed request", availability: "available", state: "queued", requestCount: 1, error: "zero performed requests" },
  { label: "queued with wrong readback state", availability: "available", state: "queued", readbackState: "UNKNOWN", error: "zero performed requests" },
  { label: "queued with readback evidence", availability: "available", state: "queued", observedAt: projectionEvidenceTimestamp, responseDigest: projectionResponseDigest, error: "without claiming readback" },
  { label: "queued retaining error", availability: "available", state: "queued", lastError: { code: "OLD" }, error: "must not retain error" },
  { label: "applied with zero attempt", availability: "available", state: "applied", attemptCount: 0, error: "positive attempt_count" },
  { label: "applied made retryable", availability: "available", state: "applied", retryable: true, nextAttemptAt: "2026-07-17T12:05:00Z", error: "must be non-retryable" },
  { label: "applied with zero requests", availability: "available", state: "applied", requestCount: 0, error: "positive exact touched-card" },
  { label: "applied with wrong readback state", availability: "available", state: "applied", readbackState: "stale", error: "positive exact touched-card" },
  { label: "applied without observation evidence", availability: "available", state: "applied", observedAt: null, responseDigest: null, error: "observed_at and response_digest" },
  { label: "applied readback before enqueue", availability: "available", state: "applied", observedAt: "2026-07-17T11:59:59Z", error: "readback cannot precede $.enqueued_at" },
  { label: "applied retaining error", availability: "available", state: "applied", lastError: { code: "OLD" }, error: "must not retain error" },
  { label: "stale with zero attempt", availability: "available", state: "stale", attemptCount: 0, error: "positive attempt_count" },
  { label: "stale with zero requests", availability: "available", state: "stale", requestCount: 0, error: "positive exact touched-card" },
  { label: "stale with wrong readback state", availability: "available", state: "stale", readbackState: "applied", error: "positive exact touched-card" },
  { label: "stale without observation evidence", availability: "available", state: "stale", observedAt: null, responseDigest: null, error: "observed_at and response_digest" },
  { label: "failed with zero attempt", availability: "available", state: "failed", attemptCount: 0, error: "positive attempt_count" },
  { label: "failed with zero requests", availability: "available", state: "failed", requestCount: 0, error: "positive exact touched-card" },
  { label: "failed with wrong readback state", availability: "available", state: "failed", readbackState: "UNKNOWN", error: "positive exact touched-card" },
  { label: "failed without error evidence", availability: "available", state: "failed", lastError: null, error: "non-empty error evidence" },
  { label: "failed with empty error evidence", availability: "available", state: "failed", lastError: {}, error: "non-empty error evidence" },
  { label: "available UNKNOWN with zero attempt", availability: "available", state: "UNKNOWN", attemptCount: 0, error: "positive attempt_count" },
  { label: "available UNKNOWN with zero requests", availability: "available", state: "UNKNOWN", requestCount: 0, error: "positive exact touched-card" },
  { label: "available UNKNOWN with wrong readback state", availability: "available", state: "UNKNOWN", readbackState: "failed", error: "positive exact touched-card" },
  { label: "available UNKNOWN without observation evidence", availability: "available", state: "UNKNOWN", observedAt: null, responseDigest: null, error: "observed_at and response_digest" },
  { label: "unavailable UNKNOWN with positive attempt", availability: "unavailable", state: "UNKNOWN", attemptCount: 1, error: "must not invent an attempt" },
  { label: "unavailable UNKNOWN with zero request claim", availability: "unavailable", state: "UNKNOWN", requestCount: 0, error: "must not invent request counts" },
  { label: "unavailable UNKNOWN with wrong readback state", availability: "unavailable", state: "UNKNOWN", readbackState: "failed", error: "must remain UNKNOWN" },
  { label: "unavailable UNKNOWN with observation evidence", availability: "unavailable", state: "UNKNOWN", observedAt: projectionEvidenceTimestamp, responseDigest: projectionResponseDigest, error: "must not invent request counts" },
  { label: "unavailable UNKNOWN missing last_error", availability: "unavailable", state: "UNKNOWN", omitLastError: true, error: "availability error evidence" },
  { label: "unavailable UNKNOWN null last_error", availability: "unavailable", state: "UNKNOWN", lastError: null, error: "availability error evidence" },
  { label: "unavailable UNKNOWN empty last_error", availability: "unavailable", state: "UNKNOWN", lastError: {}, error: "availability error evidence" },
  { label: "retryable state without next attempt", availability: "available", state: "stale", nextAttemptAt: null, error: "requires $.retry.next_attempt_at" },
  { label: "non-retryable state with next attempt", availability: "available", state: "failed", retryable: false, nextAttemptAt: "2026-07-17T12:05:00Z", error: "must not schedule a next attempt" },
];
for (const testCase of projectionDeliveryCases) {
  const candidate = makeProjectionDeliveryCase(testCase);
  assert.deepEqual(validateJsonSchema(candidate, deliverySchema.schema), [], `${testCase.label} schema`);
  const firstErrors = validateContractSemantics("atlas.projection-delivery.v1", candidate);
  const secondErrors = validateContractSemantics("atlas.projection-delivery.v1", candidate);
  assert.deepEqual(firstErrors, secondErrors, `${testCase.label} deterministic`);
  if (testCase.valid) {
    assert.deepEqual(firstErrors, [], testCase.label);
  } else {
    assert(firstErrors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${firstErrors.join(" | ")}`);
  }
}
const ackCorrelationErrors = await assertSemanticNegative(
  "atlas.projection-ack.v1",
  ackSchema.schema,
  "invalid/projection-ack.v1.mismatched-delivery.json",
  { projectionDelivery: delivery },
);
assert(ackCorrelationErrors.some((error) => error.includes("payload_digest")));
const appliedAckRetryErrors = await assertSemanticNegative(
  "atlas.projection-ack.v1",
  ackSchema.schema,
  "invalid/projection-ack.v1.applied-retry.json",
  { projectionDelivery: delivery },
);
assert(appliedAckRetryErrors.some((error) => error.includes("must be non-retryable")));
const zeroAttemptAck = await loadJson(path.join(
  fixturesDir,
  "invalid/projection-ack.v1.applied-zero-attempt.json",
));
const zeroAttemptAckSchemaErrors = validateJsonSchema(zeroAttemptAck, ackSchema.schema);
assert(zeroAttemptAckSchemaErrors.some((error) => error.includes("attempt_count")));
const missingAckAvailabilityError = await assertSemanticNegative(
  "atlas.projection-ack.v1",
  ackSchema.schema,
  "invalid/projection-ack.v1.unavailable-unknown-missing-error.json",
  { projectionDelivery: delivery },
);
assert(missingAckAvailabilityError.some((error) => error.includes("availability error evidence")));
const validUnavailableAck = await loadJson(path.join(
  fixturesDir,
  "valid/projection-ack.v1.unavailable-unknown.json",
));
assert.deepEqual(validateJsonSchema(validUnavailableAck, ackSchema.schema), []);
assert.deepEqual(
  validateContractSemantics("atlas.projection-ack.v1", validUnavailableAck, { projectionDelivery: delivery }),
  [],
);
const predatingAckErrors = await assertSemanticNegative(
  "atlas.projection-ack.v1",
  ackSchema.schema,
  "invalid/projection-ack.v1.predates-delivery.json",
  { projectionDelivery: delivery },
);
assert(predatingAckErrors.some((error) => error.includes("cannot precede ProjectionDelivery $.enqueued_at")));

const ackChronologyCases = [
  { label: "acknowledgement at enqueue", acknowledgedAt: delivery.enqueued_at, observedAt: delivery.enqueued_at, valid: true },
  { label: "acknowledgement after readback", acknowledgedAt: "2026-07-17T12:02:00Z", observedAt: "2026-07-17T12:01:00Z", valid: true },
  { label: "acknowledgement before enqueue", acknowledgedAt: "2026-07-17T11:59:59Z", observedAt: delivery.enqueued_at, error: "cannot precede ProjectionDelivery $.enqueued_at" },
  { label: "ack readback before enqueue", acknowledgedAt: "2026-07-17T12:01:00Z", observedAt: "2026-07-17T11:59:59Z", error: "readback cannot precede ProjectionDelivery $.enqueued_at" },
  { label: "acknowledgement before its readback", acknowledgedAt: delivery.enqueued_at, observedAt: "2026-07-17T12:01:00Z", error: "cannot precede its touched-card readback" },
];
for (const testCase of ackChronologyCases) {
  const candidate = structuredClone(ack);
  candidate.acknowledged_at = testCase.acknowledgedAt;
  candidate.touched_card_readback.observed_at = testCase.observedAt;
  assert.deepEqual(validateJsonSchema(candidate, ackSchema.schema), [], `${testCase.label} schema`);
  const errors = validateContractSemantics(
    "atlas.projection-ack.v1",
    candidate,
    { projectionDelivery: delivery },
  );
  if (testCase.valid) {
    assert.deepEqual(errors, [], testCase.label);
  } else {
    assert(errors.some((error) => error.includes(testCase.error)), `${testCase.label}: ${errors.join(" | ")}`);
  }
}

const duplicateControlErrors = await assertSemanticNegative(
  "atlas.control-board-read-model.v1",
  controlSchema.schema,
  "invalid/control-board-read-model.v1.duplicate-card.json",
);
assert(duplicateControlErrors.some((error) => error.includes("duplicate identity")));
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
const malformedTerminalReceipt = await loadJson(path.join(
  fixturesDir,
  "invalid/rollover-manifest.v1.malformed-terminal-receipt.json",
));
const malformedTerminalReceiptErrors = validateJsonSchema(malformedTerminalReceipt, rolloverSchema.schema);
assert(malformedTerminalReceiptErrors.some((error) => error.includes("must satisfy exactly one allowed shape")));

const rollover = validArtifacts.get("atlas.rollover-manifest.v1");
const livePredecessorRollover = structuredClone(rollover);
livePredecessorRollover.predecessor_epoch.status = "active";
assert(validateContractSemantics("atlas.rollover-manifest.v1", livePredecessorRollover).some(
  (error) => error.includes("identified terminal receipt"),
));

console.log(
  `ATLAS board authority contract tests passed (${archiveTransitionCases.length} lifecycle, ${receiptCases.length} receipt, ${eventVersionCases.length} version, ${projectionDeliveryCases.length} projection, ${ackChronologyCases.length} acknowledgement chronology, ${controlIdentityCases.length} control identity matrix cases).`,
);
