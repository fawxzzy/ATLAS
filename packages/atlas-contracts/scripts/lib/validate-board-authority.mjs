const COMMIT_CLOSURE_ORDER = Object.freeze([
  "validate-execution-receipt",
  "idempotency-lookup",
  "expected-version-cas",
  "append-card-event",
  "materialize-card-record",
  "enqueue-projection-delivery",
  "persist-board-commit-receipt",
  "commit-transaction",
]);

const TARGET_CONTRACTS = Object.freeze([
  "atlas.card-record.v3",
  "atlas.card-event.v3",
  "atlas.board-commit-receipt.v1",
  "atlas.projection-delivery.v1",
  "atlas.projection-ack.v1",
  "atlas.board-authority-migration.v1",
  "atlas.control-board-read-model.v1",
  "atlas.rollover-manifest.v1",
]);

function duplicateValues(values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates];
}

function sameArray(actual, expected) {
  return actual.length === expected.length
    && actual.every((value, index) => value === expected[index]);
}

function isNonEmptyObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length > 0;
}

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function validateArchiveMaterialization({ lifecycle, archiveState, standingAnchor }) {
  const errors = [];
  if (standingAnchor === true && (lifecycle === "archived" || archiveState === "archived")) {
    errors.push("Stable standing anchors must remain unarchived");
  }
  if (lifecycle !== undefined
    && archiveState !== undefined
    && ((lifecycle === "archived") !== (archiveState === "archived"))) {
    errors.push("Lifecycle archived and archive_state archived must move together");
  }
  return errors;
}

export function projectInitialCardRecordV3(event) {
  const set = event.changes.set;
  return {
    contract_version: "atlas.card-record.v3",
    authority: event.authority,
    card_id: event.card_id,
    project_id: event.project_id,
    board_id: event.board_id,
    epoch_id: set.epoch_id,
    version: event.card_version,
    last_event_sequence: event.event_sequence,
    title: set.title,
    description: set.description,
    card_type: set.card_type,
    lifecycle: set.lifecycle,
    priority: set.priority,
    owner: set.owner,
    standing_anchor: set.standing_anchor,
    archive_state: set.archive_state,
    work: set.work,
    blockers: event.changes.add_blockers,
    owned_resources: event.changes.add_resources,
    receipt_refs: event.changes.add_receipts.map((receipt) => ({
      ...receipt,
      status: receipt.receipt_id === event.execution_receipt.receipt_id
        && receipt.digest === event.execution_receipt.digest
        ? "succeeded"
        : "UNKNOWN",
    })),
    next_action: set.next_action,
    projection_state: set.projection_state,
    created_at: event.occurred_at,
    updated_at: event.occurred_at,
  };
}

export function validateCardRecordV3(record) {
  const errors = [];
  if (record.last_event_sequence < record.version) {
    errors.push("$.last_event_sequence cannot precede $.version");
  }
  errors.push(...validateArchiveMaterialization({
    lifecycle: record.lifecycle,
    archiveState: record.archive_state,
    standingAnchor: record.standing_anchor,
  }));
  if (Date.parse(record.updated_at) < Date.parse(record.created_at)) {
    errors.push("$.updated_at cannot precede $.created_at");
  }
  for (const duplicate of duplicateValues(record.blockers.map((item) => item.blocker_id))) {
    errors.push(`$.blockers contains duplicate blocker_id ${duplicate}`);
  }
  for (const duplicate of duplicateValues(record.owned_resources.map((item) => item.resource_id))) {
    errors.push(`$.owned_resources contains duplicate resource_id ${duplicate}`);
  }
  for (const duplicate of duplicateValues(record.receipt_refs.map((item) => item.receipt_id))) {
    errors.push(`$.receipt_refs contains duplicate receipt_id ${duplicate}`);
  }
  return errors;
}

export function validateCardEventV3(event) {
  const errors = [];
  if (event.card_version !== event.expected_version + 1) {
    errors.push("$.card_version must equal $.expected_version + 1");
  }
  if (event.event_sequence < event.card_version) {
    errors.push("$.event_sequence cannot precede $.card_version");
  }
  const isInitial = event.event_type === "create" || event.event_type === "baseline-import";
  if (isInitial && (event.expected_version !== 0 || event.previous_record_digest !== null)) {
    errors.push("Initial create/import events require expected_version 0 and null previous_record_digest");
  }
  if (!isInitial && event.previous_record_digest === null) {
    errors.push("Non-initial events require a previous_record_digest");
  }
  if (!isInitial && event.expected_version < 1) {
    errors.push("Non-initial events require $.expected_version >= 1");
  }
  if (isInitial) {
    const requiredInitialFields = [
      "epoch_id",
      "title",
      "description",
      "card_type",
      "lifecycle",
      "priority",
      "owner",
      "standing_anchor",
      "archive_state",
      "work",
      "next_action",
      "projection_state",
    ];
    let initialFieldsComplete = true;
    for (const field of requiredInitialFields) {
      if (!(field in event.changes.set)) {
        errors.push(`Initial create/import event requires $.changes.set.${field}`);
        initialFieldsComplete = false;
      }
    }
    if (event.changes.transition?.from !== null || event.changes.transition?.to !== event.changes.set.lifecycle) {
      errors.push("Initial create/import transition must move from null to the materialized lifecycle");
    }
    if (initialFieldsComplete) {
      errors.push(...validateCardRecordV3(projectInitialCardRecordV3(event)).map(
        (error) => `Initial materialized CardRecord: ${error}`,
      ));
    }
  }
  if (event.changes.set.epoch_id !== undefined && event.changes.set.epoch_id !== event.epoch_id) {
    errors.push("$.changes.set.epoch_id must equal $.epoch_id");
  }
  const changes = event.changes;
  const hasChange = isNonEmptyObject(changes.set)
    || changes.transition !== null
    || changes.add_blockers.length > 0
    || changes.remove_blocker_ids.length > 0
    || changes.add_resources.length > 0
    || changes.remove_resource_ids.length > 0
    || changes.add_receipts.length > 0;
  if (!hasChange) errors.push("$.changes must contain at least one deterministic materialization operation");
  if (event.event_type === "transition" && changes.transition === null) {
    errors.push("Transition events require $.changes.transition");
  }
  if (!isInitial && changes.transition?.from === null) {
    errors.push("Non-initial transitions require a lifecycle-valued $.changes.transition.from");
  }
  if (changes.transition !== null
    && changes.set.lifecycle !== undefined
    && changes.set.lifecycle !== changes.transition.to) {
    errors.push("$.changes.set.lifecycle must equal $.changes.transition.to when both materialization operations are present");
  }
  if (!isInitial) {
    const crossesArchivedBoundary = changes.transition !== null
      && ((changes.transition.from === "archived") !== (changes.transition.to === "archived"));
    if (crossesArchivedBoundary && changes.set.archive_state === undefined) {
      errors.push("Transitions crossing the archived boundary require $.changes.set.archive_state");
    }
    if (changes.transition?.to === "archived" && changes.transition.from !== "archived"
      && changes.set.standing_anchor !== false) {
      errors.push("A transition into archived requires explicit $.changes.set.standing_anchor false");
    }
    errors.push(...validateArchiveMaterialization({
      lifecycle: changes.transition?.to ?? changes.set.lifecycle,
      archiveState: changes.set.archive_state,
      standingAnchor: changes.set.standing_anchor,
    }));
  }
  for (const key of ["remove_blocker_ids", "remove_resource_ids"]) {
    for (const duplicate of duplicateValues(changes[key])) {
      errors.push(`$.changes.${key} contains duplicate id ${duplicate}`);
    }
  }
  const addCollections = [
    ["add_blockers", "blocker_id"],
    ["add_resources", "resource_id"],
    ["add_receipts", "receipt_id"],
  ];
  for (const [collection, idField] of addCollections) {
    for (const duplicate of duplicateValues(changes[collection].map((item) => item[idField]))) {
      errors.push(`$.changes.${collection} contains duplicate ${idField} ${duplicate}`);
    }
  }
  for (const receipt of changes.add_receipts) {
    if (receipt.receipt_id === event.execution_receipt.receipt_id
      && receipt.digest !== event.execution_receipt.digest) {
      errors.push("An added execution receipt reference must match $.execution_receipt identity and digest");
    }
  }
  const blockerRemovals = new Set(changes.remove_blocker_ids);
  for (const blocker of changes.add_blockers) {
    if (blockerRemovals.has(blocker.blocker_id)) {
      errors.push(`$.changes cannot add and remove blocker_id ${blocker.blocker_id} in one event`);
    }
  }
  const resourceRemovals = new Set(changes.remove_resource_ids);
  for (const resource of changes.add_resources) {
    if (resourceRemovals.has(resource.resource_id)) {
      errors.push(`$.changes cannot add and remove resource_id ${resource.resource_id} in one event`);
    }
  }
  return errors;
}

export function validateBoardCommitReceiptV1(receipt) {
  const errors = [];
  if (!sameArray(receipt.closure_order, COMMIT_CLOSURE_ORDER)) {
    errors.push(`$.closure_order must exactly equal ${COMMIT_CLOSURE_ORDER.join(" -> ")}`);
  }
  if (receipt.card_version !== receipt.expected_version + 1) {
    errors.push("$.card_version must equal $.expected_version + 1");
  }
  if (receipt.projection_gates_engineering !== false || receipt.engineering_closed !== true) {
    errors.push("Accepted local commit must close engineering without projection gating");
  }
  return errors;
}

function validateProjectionState(value, { allowQueued, availabilityError }) {
  const errors = [];
  const readback = value.touched_card_readback;
  if (readback.card_id !== value.card_id) {
    errors.push("$.touched_card_readback.card_id must equal $.card_id");
  }
  if (value.availability === "unavailable") {
    if (value.state !== "UNKNOWN" || readback.state !== "UNKNOWN") {
      errors.push("Unavailable projection evidence must remain UNKNOWN");
    }
    if (readback.request_count !== null || readback.observed_at !== null || readback.response_digest !== null) {
      errors.push("Unavailable projection readback must not invent request counts, timestamps, or response digests");
    }
    if (!isNonEmptyObject(availabilityError)) {
      errors.push("Unavailable projection requires non-empty availability error evidence");
    }
  }
  if (value.availability === "available" && value.state === "UNKNOWN") {
    if (readback.state !== "UNKNOWN" || !isPositiveInteger(readback.request_count)) {
      errors.push("Available UNKNOWN projection requires positive exact touched-card request-count proof with UNKNOWN readback state");
    }
    if (readback.observed_at === null || readback.response_digest === null) {
      errors.push("Available UNKNOWN projection requires observed_at and response_digest");
    }
  }
  if (value.state === "applied") {
    if (readback.state !== "applied" || !isPositiveInteger(readback.request_count)) {
      errors.push("Applied projection requires positive exact touched-card request-count proof");
    }
    if (readback.observed_at === null || readback.response_digest === null) {
      errors.push("Applied projection requires observed_at and response_digest");
    }
  }
  if (value.state === "stale") {
    if (readback.state !== "stale" || !isPositiveInteger(readback.request_count)) {
      errors.push("Stale projection requires positive exact touched-card request-count proof");
    }
    if (readback.observed_at === null || readback.response_digest === null) {
      errors.push("Stale projection requires observed_at and response_digest");
    }
  }
  if (value.state === "failed" && (readback.state !== "failed" || !isPositiveInteger(readback.request_count))) {
    errors.push("Failed projection requires positive exact touched-card request-count proof");
  }
  if (value.state === "failed" && !isNonEmptyObject(availabilityError)) {
    errors.push("Failed projection requires non-empty error evidence");
  }
  if ((value.state === "queued" || value.state === "applied")
    && availabilityError !== null && availabilityError !== undefined) {
    errors.push(`${value.state === "queued" ? "Queued" : "Applied"} projection must not retain error evidence`);
  }
  if (allowQueued && value.state === "queued") {
    if (readback.state !== "queued" || readback.request_count !== 0 || readback.observed_at !== null || readback.response_digest !== null) {
      errors.push("Queued projection must expose zero performed requests without claiming readback");
    }
  }
  return errors;
}

export function validateProjectionDeliveryV1(delivery) {
  const errors = validateProjectionState(delivery, {
    allowQueued: true,
    availabilityError: delivery.last_error,
  });
  if (delivery.retry.retryable && delivery.retry.next_attempt_at === null) {
    errors.push("Retryable delivery requires $.retry.next_attempt_at");
  }
  if (!delivery.retry.retryable && delivery.retry.next_attempt_at !== null) {
    errors.push("Non-retryable delivery must not schedule a next attempt");
  }
  if (delivery.state === "queued" && delivery.retry.attempt_count !== 0) {
    errors.push("Newly queued delivery must start at attempt_count 0");
  }
  if (delivery.state === "queued" && !delivery.retry.retryable) {
    errors.push("Queued projection delivery must remain retryable");
  }
  if (delivery.availability === "unavailable" && delivery.retry.attempt_count !== 0) {
    errors.push("Unavailable UNKNOWN delivery must not invent an attempt");
  }
  const requiresPositiveAttempt = ["applied", "stale", "failed"].includes(delivery.state)
    || (delivery.state === "UNKNOWN" && delivery.availability === "available");
  if (requiresPositiveAttempt && !isPositiveInteger(delivery.retry.attempt_count)) {
    errors.push("Post-queued projection delivery requires a positive attempt_count");
  }
  if (delivery.state === "applied" && (delivery.retry.retryable || delivery.retry.next_attempt_at !== null)) {
    errors.push("Applied projection delivery must be non-retryable with no next attempt");
  }
  if (delivery.touched_card_readback.observed_at !== null
    && Date.parse(delivery.touched_card_readback.observed_at) < Date.parse(delivery.enqueued_at)) {
    errors.push("ProjectionDelivery readback cannot precede $.enqueued_at");
  }
  return errors;
}

export function validateProjectionAckV1(ack, context = {}) {
  const errors = validateProjectionState(ack, {
    allowQueued: false,
    availabilityError: ack.error,
  });
  if (ack.retryable && ack.next_attempt_at === null) {
    errors.push("Retryable acknowledgement requires $.next_attempt_at");
  }
  if (!ack.retryable && ack.next_attempt_at !== null) {
    errors.push("Non-retryable acknowledgement must not schedule a next attempt");
  }
  if (ack.state === "applied" && (ack.retryable || ack.next_attempt_at !== null)) {
    errors.push("Applied projection acknowledgement must be non-retryable with no next attempt");
  }
  if (!isPositiveInteger(ack.attempt_count)) {
    errors.push("Projection acknowledgement requires a positive attempt_count");
  }
  if (context.projectionDeliveryError) {
    errors.push(context.projectionDeliveryError);
  } else if (!context.projectionDelivery) {
    errors.push("ProjectionAck admission requires the referenced ProjectionDelivery context");
  } else {
    errors.push(...validateProjectionAckAgainstDelivery(ack, context.projectionDelivery));
  }
  return errors;
}

export function validateProjectionAckAgainstDelivery(ack, delivery) {
  const errors = [];
  const correlatedFields = [
    ["delivery_id", "delivery_id"],
    ["card_id", "card_id"],
    ["project_id", "project_id"],
    ["board_id", "board_id"],
    ["event_id", "event_id"],
    ["event_sequence", "event_sequence"],
    ["card_version", "card_version"],
    ["idempotency_key", "idempotency_key"],
    ["payload_digest", "payload_digest"],
  ];
  for (const [ackField, deliveryField] of correlatedFields) {
    if (ack[ackField] !== delivery[deliveryField]) {
      errors.push(`ProjectionAck $.${ackField} must equal ProjectionDelivery $.${deliveryField}`);
    }
  }
  if (Date.parse(ack.acknowledged_at) < Date.parse(delivery.enqueued_at)) {
    errors.push("ProjectionAck $.acknowledged_at cannot precede ProjectionDelivery $.enqueued_at");
  }
  if (ack.touched_card_readback.observed_at !== null) {
    if (Date.parse(ack.touched_card_readback.observed_at) < Date.parse(delivery.enqueued_at)) {
      errors.push("ProjectionAck readback cannot precede ProjectionDelivery $.enqueued_at");
    }
    if (Date.parse(ack.acknowledged_at) < Date.parse(ack.touched_card_readback.observed_at)) {
      errors.push("ProjectionAck $.acknowledged_at cannot precede its touched-card readback");
    }
  }
  return errors;
}

export function validateBoardAuthorityMigrationV1(migration) {
  const errors = [];
  if (!sameArray(migration.target_contracts, TARGET_CONTRACTS)) {
    errors.push(`$.target_contracts must exactly freeze ${TARGET_CONTRACTS.join(", ")}`);
  }
  if (migration.v2_authority_snapshot.status === "UNKNOWN") {
    const source = migration.v2_authority_snapshot;
    if (source.snapshot_id !== null || source.digest !== null || source.captured_at !== null || !source.unknown_reason) {
      errors.push("UNKNOWN v2 authority snapshot must carry only an explicit unknown_reason");
    }
  }
  if (migration.v2_authority_snapshot.status === "available") {
    const source = migration.v2_authority_snapshot;
    if (!source.snapshot_id || !source.digest || !source.captured_at || source.unknown_reason !== null) {
      errors.push("Available v2 authority snapshot requires exact identity, digest, timestamp, and null unknown_reason");
    }
  }
  const baselineImport = migration.one_time_import;
  if (baselineImport.status === "not-started") {
    if (baselineImport.source_snapshot_digest !== null
      || baselineImport.event_sequence_start !== null
      || baselineImport.event_sequence_end !== null
      || baselineImport.imported_at !== null
      || baselineImport.failure_reason !== null
      || baselineImport.unknown_reason !== null) {
      errors.push("Not-started one-time import must not claim source, sequence, or timestamp evidence");
    }
  }
  if (["imported", "verified"].includes(baselineImport.status)) {
    if (!baselineImport.source_snapshot_digest
      || !isPositiveInteger(baselineImport.event_sequence_start)
      || !isPositiveInteger(baselineImport.event_sequence_end)
      || baselineImport.event_sequence_end < baselineImport.event_sequence_start
      || !baselineImport.imported_at
      || baselineImport.failure_reason !== null
      || baselineImport.unknown_reason !== null) {
      errors.push("Imported baseline requires source digest, ordered event sequence, and imported_at");
    }
  }
  if (baselineImport.status === "failed") {
    if (!baselineImport.source_snapshot_digest
      || baselineImport.event_sequence_start !== null
      || baselineImport.event_sequence_end !== null
      || baselineImport.imported_at !== null
      || !baselineImport.failure_reason
      || baselineImport.unknown_reason !== null) {
      errors.push("Failed baseline import requires source digest and failure reason without committed sequence evidence");
    }
  }
  if (baselineImport.status === "UNKNOWN") {
    if (!baselineImport.source_snapshot_digest
      || baselineImport.event_sequence_start !== null
      || baselineImport.event_sequence_end !== null
      || baselineImport.imported_at !== null
      || baselineImport.failure_reason !== null
      || !baselineImport.unknown_reason) {
      errors.push("UNKNOWN baseline import requires source digest and unknown reason without invented sequence evidence");
    }
  }
  const accepted = migration.first_v3_acceptance.status === "accepted";
  if (!accepted) {
    if (migration.first_v3_acceptance.receipt_id !== null || migration.first_v3_acceptance.accepted_at !== null) {
      errors.push("Not-accepted v3 state must not claim a first acceptance receipt or timestamp");
    }
    if (migration.rollback.current_mode !== "v2-authority-allowed") {
      errors.push("Before first v3 acceptance, current rollback mode must allow explicit v2 authority return");
    }
  } else {
    if (!migration.first_v3_acceptance.receipt_id || !migration.first_v3_acceptance.accepted_at) {
      errors.push("Accepted v3 state requires the first BoardCommitReceipt identity and timestamp");
    }
    if (baselineImport.status !== "verified") {
      errors.push("First v3 acceptance requires verified one-time baseline import");
    }
    if (migration.rollback.current_mode !== "v3-restore-replay-only") {
      errors.push("After first v3 acceptance, rollback is v3 restore/replay only; silent v2 authority reversion is forbidden");
    }
  }
  if (migration.phase === "planned" && migration.cutover.status !== "held") {
    errors.push("Planned migration must keep cutover held");
  }
  if (["imported", "verified", "failed", "UNKNOWN"].includes(baselineImport.status)
    && baselineImport.source_snapshot_digest !== migration.v2_authority_snapshot.digest) {
    errors.push("One-time import source digest must equal the available v2 authority snapshot digest");
  }
  const phaseRequirements = {
    planned: {
      importStatuses: ["not-started"],
      accepted: false,
      rollback: "v2-authority-allowed",
      cutover: ["held"],
    },
    "baseline-imported": {
      importStatuses: ["imported", "verified"],
      accepted: false,
      rollback: "v2-authority-allowed",
      cutover: ["held"],
    },
    "baseline-import-failed": {
      importStatuses: ["failed"],
      accepted: false,
      rollback: "v2-authority-allowed",
      cutover: ["held"],
    },
    "baseline-import-unknown": {
      importStatuses: ["UNKNOWN"],
      accepted: false,
      rollback: "v2-authority-allowed",
      cutover: ["held"],
    },
    "v3-acceptance-open": {
      importStatuses: ["verified"],
      accepted: false,
      rollback: "v2-authority-allowed",
      cutover: ["ready"],
    },
    "v3-active": {
      importStatuses: ["verified"],
      accepted: true,
      rollback: "v3-restore-replay-only",
      cutover: ["active"],
    },
    "rolled-back-v3": {
      importStatuses: ["verified"],
      accepted: true,
      rollback: "v3-restore-replay-only",
      cutover: ["rolled-back-v3"],
    },
  };
  const required = phaseRequirements[migration.phase];
  if (!required.importStatuses.includes(baselineImport.status)
    || required.accepted !== accepted
    || required.rollback !== migration.rollback.current_mode
    || !required.cutover.includes(migration.cutover.status)) {
    errors.push(`Migration phase ${migration.phase} is inconsistent with import, acceptance, rollback, or cutover state`);
  }
  if (migration.phase !== "planned" && migration.v2_authority_snapshot.status !== "available") {
    errors.push(`Migration phase ${migration.phase} requires an available v2 authority snapshot`);
  }
  return errors;
}

export function validateControlBoardReadModelV1(model) {
  const errors = [];
  const summaryKeys = ["queued", "applied", "stale", "failed", "UNKNOWN"];
  const cardIdentities = model.cards.map((card) => JSON.stringify([
    card.project_id,
    card.board_id,
    card.card_id,
  ]));
  for (const duplicate of duplicateValues(cardIdentities)) {
    const [projectId, boardId, cardId] = JSON.parse(duplicate);
    errors.push(`$.cards contains duplicate identity ${projectId}/${boardId}/${cardId}`);
  }
  if (model.availability === "unavailable") {
    if (model.card_count !== null || summaryKeys.some((key) => model.projection_summary[key] !== null)) {
      errors.push("Unavailable read model must use null counts, never inferred zero or health");
    }
    if (model.unknowns.length === 0) errors.push("Unavailable read model requires explicit unknown reasons");
    if (model.cards.some((card) => card.projection_state !== "UNKNOWN")) {
      errors.push("Unavailable read model cannot claim a known card projection state");
    }
    return errors;
  }
  if (model.card_count !== model.cards.length) {
    errors.push("$.card_count must equal the generated card projection count");
  }
  const actual = Object.fromEntries(summaryKeys.map((key) => [key, 0]));
  for (const card of model.cards) actual[card.projection_state] += 1;
  for (const key of summaryKeys) {
    if (model.projection_summary[key] !== actual[key]) {
      errors.push(`$.projection_summary.${key} must equal ${actual[key]}`);
    }
  }
  if (model.availability === "partial" && model.unknowns.length === 0) {
    errors.push("Partial read model requires explicit unknown reasons");
  }
  return errors;
}

export function validateRolloverManifestV1(manifest) {
  const errors = [];
  if (manifest.predecessor_epoch.card_id !== manifest.card_id || manifest.successor_epoch.card_id !== manifest.card_id) {
    errors.push("Predecessor and successor epochs must correlate to $.card_id");
  }
  if (manifest.predecessor_epoch.epoch_id === manifest.successor_epoch.epoch_id) {
    errors.push("Predecessor and successor epoch identities must differ");
  }
  if (manifest.successor_reconstruction.context_digest !== manifest.context_digest) {
    errors.push("Successor reconstruction context digest must equal the manifest context digest");
  }
  for (const duplicate of duplicateValues(manifest.receipt_digests)) {
    errors.push(`$.receipt_digests contains duplicate digest ${duplicate}`);
  }
  const archiveState = manifest.archive_gate.predecessor_epoch_archive;
  if (archiveState === "eligible" || archiveState === "archived") {
    if (manifest.predecessor_epoch.status !== "terminal"
      || manifest.terminal_receipt === null
      || manifest.terminal_receipt?.epoch_id !== manifest.predecessor_epoch.epoch_id
      || manifest.terminal_receipt?.status !== "terminal"
      || !manifest.receipt_digests.includes(manifest.terminal_receipt?.digest)
      || manifest.successor_reconstruction.status !== "verified"
      || manifest.successor_reconstruction.exact_readback !== "verified"
      || manifest.successor_reconstruction.reconstructed_at === null
      || manifest.successor_epoch.status !== "reconstructed"
      || !manifest.archive_gate.successor_continuity_verified
      || !manifest.archive_gate.exact_readback_verified) {
      errors.push("Bounded predecessor epoch cannot archive before an identified terminal receipt for that epoch, verified successor reconstruction, continuity, and exact readback");
    }
  }
  return errors;
}

export const boardAuthoritySemanticValidators = Object.freeze({
  "atlas.card-record.v3": validateCardRecordV3,
  "atlas.card-event.v3": validateCardEventV3,
  "atlas.board-commit-receipt.v1": validateBoardCommitReceiptV1,
  "atlas.projection-delivery.v1": validateProjectionDeliveryV1,
  "atlas.projection-ack.v1": validateProjectionAckV1,
  "atlas.board-authority-migration.v1": validateBoardAuthorityMigrationV1,
  "atlas.control-board-read-model.v1": validateControlBoardReadModelV1,
  "atlas.rollover-manifest.v1": validateRolloverManifestV1,
});

export { COMMIT_CLOSURE_ORDER, TARGET_CONTRACTS };
