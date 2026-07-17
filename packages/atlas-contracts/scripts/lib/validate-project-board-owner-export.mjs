import path from "node:path";

function uniqueDuplicates(values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates].sort();
}

function isRelativePortablePath(value) {
  if (typeof value !== "string" || value.trim() === "") return false;
  const normalized = value.replaceAll("\\", "/");
  if (path.win32.isAbsolute(value) || path.posix.isAbsolute(normalized)) return false;
  return !normalized.split("/").some((segment) => segment === "." || segment === "..");
}

function requireRelationship(errors, card, field, expectedStatus) {
  const value = card.relationships?.[field];
  if (card.record_status === expectedStatus && !value) {
    errors.push(`$.cards[${card.index}].relationships.${field} is required when record_status is ${expectedStatus}`);
  }
  if (card.record_status !== expectedStatus && value) {
    errors.push(`$.cards[${card.index}].relationships.${field} is only allowed when record_status is ${expectedStatus}`);
  }
  if (value && value === card.record?.card_id) {
    errors.push(`$.cards[${card.index}].relationships.${field} must not reference the same card`);
  }
}

function validateRuntimeReadback(errors, value, sourceIdSet) {
  const readback = value.runtime_readback;
  const hasRuntimeSource = sourceIdSet.has("atlas-runtime-placement-registry");
  if (!readback) {
    if (hasRuntimeSource) {
      errors.push("$.runtime_readback is required when the runtime placement source is present");
    }
    return;
  }
  if (!hasRuntimeSource) {
    errors.push("$.runtime_readback requires source_id atlas-runtime-placement-registry in $.sources");
    return;
  }

  const runtimeSource = value.sources.find((source) => source.source_id === readback.source_id);
  if (runtimeSource?.path !== readback.source_ref) {
    errors.push("$.runtime_readback.source_ref must equal the runtime source path");
  }
  if (runtimeSource?.revision !== readback.source_revision) {
    errors.push("$.runtime_readback.source_revision must equal the runtime source revision");
  }
  if (!isRelativePortablePath(readback.source_ref)) {
    errors.push("$.runtime_readback.source_ref must be an ATLAS-relative portable path");
  }

  const sequence = Array.isArray(readback.activation_sequence) ? readback.activation_sequence : [];
  const steps = Array.isArray(readback.activation_steps) ? readback.activation_steps : [];
  const stepIds = steps.map((step) => step.id);
  if (JSON.stringify(stepIds) !== JSON.stringify(sequence)) {
    errors.push("$.runtime_readback.activation_steps must map one-to-one and in order to activation_sequence");
  }
  for (const duplicate of uniqueDuplicates(stepIds)) {
    errors.push(`$.runtime_readback.activation_steps contains duplicate id ${JSON.stringify(duplicate)}`);
  }

  let expectedSelector = null;
  let unresolvedSeen = false;
  steps.forEach((step, index) => {
    if (step.order !== index + 1) {
      errors.push(`$.runtime_readback.activation_steps[${index}].order must equal ${index + 1}`);
    }
    if (step.status === "accepted") {
      if (unresolvedSeen) {
        errors.push("$.runtime_readback accepted activation steps must form a contiguous prefix");
      }
      return;
    }
    unresolvedSeen = true;
    if (expectedSelector === null) expectedSelector = step.packet;
  });
  if (readback.selector !== expectedSelector) {
    errors.push("$.runtime_readback.selector must equal the first non-accepted activation packet or null");
  }

  const boundaries = readback.status_boundaries ?? {};
  for (const status of ["pending", "blocked"]) {
    const expected = steps.filter((step) => step.status === status).map((step) => step.id);
    if (JSON.stringify(boundaries[status] ?? []) !== JSON.stringify(expected)) {
      errors.push(`$.runtime_readback.status_boundaries.${status} must exactly match activation step status`);
    }
  }

  const markers = Array.isArray(readback.marker_lanes) ? readback.marker_lanes : [];
  for (const duplicate of uniqueDuplicates(markers.map((marker) => marker.id))) {
    errors.push(`$.runtime_readback.marker_lanes contains duplicate id ${JSON.stringify(duplicate)}`);
  }
  markers.forEach((marker, markerIndex) => {
    const units = Array.isArray(marker.units) ? marker.units : [];
    if (units.length !== marker.denominator) {
      errors.push(
        `$.runtime_readback.marker_lanes[${markerIndex}].units length must equal the fixed denominator`,
      );
    }
    for (const duplicate of uniqueDuplicates(units.map((unit) => unit.id))) {
      errors.push(`$.runtime_readback.marker_lanes[${markerIndex}].units contains duplicate id ${JSON.stringify(duplicate)}`);
    }
    const accepted = units.filter((unit) => unit.status === "accepted").length;
    const expectedCompleted = accepted || null;
    const expectedPercentage = accepted ? (accepted * 100) / marker.denominator : null;
    if (marker.completed_units !== expectedCompleted || marker.percentage !== expectedPercentage) {
      errors.push(`$.runtime_readback.marker_lanes[${markerIndex}] counts must derive from accepted units`);
    }
  });
}

export function validateProjectBoardOwnerExport(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];

  const errors = [];
  const sources = Array.isArray(value.sources) ? value.sources : [];
  const cards = Array.isArray(value.cards) ? value.cards : [];
  const sourceIds = sources.map((source) => source.source_id);
  const sourceIdSet = new Set(sourceIds);

  for (const duplicate of uniqueDuplicates(sourceIds)) {
    errors.push(`$.sources contains duplicate source_id ${JSON.stringify(duplicate)}`);
  }
  sources.forEach((source, index) => {
    if (!isRelativePortablePath(source.path)) {
      errors.push(`$.sources[${index}].path must be an ATLAS-relative portable path`);
    }
  });
  validateRuntimeReadback(errors, value, sourceIdSet);

  const indexedCards = cards.map((card, index) => ({ ...card, index }));
  for (const duplicate of uniqueDuplicates(indexedCards.map((card) => card.record?.card_id))) {
    errors.push(`$.cards contains duplicate card_id ${JSON.stringify(duplicate)}`);
  }
  for (const duplicate of uniqueDuplicates(indexedCards.map((card) => card.idempotency_key))) {
    errors.push(`$.cards contains duplicate idempotency_key ${JSON.stringify(duplicate)}`);
  }

  for (const card of indexedCards) {
    const at = `$.cards[${card.index}]`;
    const record = card.record ?? {};
    const source = card.source ?? {};
    const content = card.content ?? {};

    if (record.project_id !== value.project_id) {
      errors.push(`${at}.record.project_id must equal $.project_id`);
    }
    if (record.board_id !== value.board_id) {
      errors.push(`${at}.record.board_id must equal $.board_id`);
    }
    if (!sourceIdSet.has(source.source_id)) {
      errors.push(`${at}.source.source_id must reference $.sources`);
    }
    if (record.source_ref !== source.source_ref) {
      errors.push(`${at}.record.source_ref must equal ${at}.source.source_ref`);
    }
    if (!isRelativePortablePath(source.source_ref)) {
      errors.push(`${at}.source.source_ref must be an ATLAS-relative portable path`);
    }
    if (uniqueDuplicates(record.dependencies ?? []).length > 0) {
      errors.push(`${at}.record.dependencies must not contain duplicates`);
    }
    if ((record.dependencies ?? []).includes(record.card_id)) {
      errors.push(`${at}.record.dependencies must not reference the same card`);
    }

    requireRelationship(errors, card, "duplicate_of", "duplicate");
    requireRelationship(errors, card, "superseded_by", "superseded");

    if (["ready", "in-progress", "review", "completed"].includes(record.lifecycle)) {
      if (!content.objective?.trim()) {
        errors.push(`${at}.content.objective is required for lifecycle ${record.lifecycle}`);
      }
      if (!Array.isArray(content.acceptance_criteria) || content.acceptance_criteria.length === 0) {
        errors.push(`${at}.content.acceptance_criteria must not be empty for lifecycle ${record.lifecycle}`);
      }
    }
    if (record.lifecycle === "ready" && (content.blockers?.length ?? 0) > 0) {
      errors.push(`${at}.content.blockers must be empty when lifecycle is ready`);
    }
  }

  return errors;
}
